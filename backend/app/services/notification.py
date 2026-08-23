from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

import resend
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Notification, User

settings = get_settings()

# Configure Resend
if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY

# Configure Twilio
twilio_client = None
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


class NotificationService:
    """Service for sending notifications (email/SMS)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: UUID,
        order_id: Optional[UUID],
        type: str,  # email, sms
        subject: Optional[str],
        message: str
    ) -> Notification:
        """Create a notification record"""
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            order_id=order_id,
            type=type,
            subject=subject,
            message=message,
            status="pending",
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def send_notification(self, notification_id: UUID) -> bool:
        """Send notification via external provider (Resend/Twilio)"""
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return False

        try:
            if notification.type == "email":
                success = await self._send_email(notification)
            elif notification.type == "sms":
                success = await self._send_sms(notification)
            else:
                success = False

            notification.status = "sent" if success else "failed"
            notification.sent_at = datetime.utcnow()
            await self.db.commit()
            return success
        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            await self.db.commit()
            return False

    async def _send_email(self, notification: Notification) -> bool:
        """Send email via Resend"""
        if not settings.RESEND_API_KEY:
            print("Resend API key not configured, skipping email")
            return False

        # Get user email
        result = await self.db.execute(
            select(User).where(User.id == notification.user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.email:
            print(f"No email for user {notification.user_id}")
            return False

        try:
            response = resend.Emails.send({
                "from": settings.EMAIL_FROM,
                "to": user.email,
                "subject": notification.subject or "Delivery Update",
                "html": notification.message,
            })
            notification.external_id = response.get("id")
            return True
        except Exception as e:
            notification.error_message = f"Resend error: {str(e)}"
            return False

    async def _send_sms(self, notification: Notification) -> bool:
        """Send SMS via Twilio"""
        if not twilio_client or not settings.TWILIO_PHONE_NUMBER:
            print("Twilio not configured, skipping SMS")
            return False

        # Get user phone
        result = await self.db.execute(
            select(User).where(User.id == notification.user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.phone:
            print(f"No phone for user {notification.user_id}")
            return False

        try:
            message = twilio_client.messages.create(
                body=notification.message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=user.phone
            )
            notification.external_id = message.sid
            return True
        except Exception as e:
            notification.error_message = f"Twilio error: {str(e)}"
            return False

    async def notify_order_status_change(
        self,
        order_id: UUID,
        old_status: Optional[str],
        new_status: str,
        actor_role: str
    ):
        """Send notifications for order status change"""
        from app.services.order import OrderService
        order_service = OrderService(self.db)
        order = await order_service.get_order(order_id)

        if not order:
            return

        # Get customer
        customer = order.customer
        if not customer:
            return

        status_messages = {
            "created": "Your order has been created and is awaiting pickup.",
            "picked_up": "Your order has been picked up by the delivery agent.",
            "in_transit": "Your order is in transit to the destination.",
            "out_for_delivery": "Your order is out for delivery and will arrive soon.",
            "delivered": "Your order has been successfully delivered!",
            "failed": "Delivery attempt failed. You can reschedule from the app.",
            "cancelled": "Your order has been cancelled.",
        }

        subject = f"Order {order.order_number} - {new_status.replace('_', ' ').title()}"
        message = f"""
        <h2>Order Update</h2>
        <p>Order: <strong>{order.order_number}</strong></p>
        <p>Status: <strong>{new_status.replace('_', ' ').title()}</strong></p>
        <p>{status_messages.get(new_status, 'Your order status has been updated.')}</p>
        <p><a href="{settings.FRONTEND_URL}/orders/{order.id}">Track your order</a></p>
        """

        # Create and send email
        email_notification = await self.create_notification(
            user_id=customer.id,
            order_id=order_id,
            type="email",
            subject=subject,
            message=message
        )
        await self.send_notification(email_notification.id)

        # Create and send SMS if phone available
        if customer.phone:
            sms_message = f"Order {order.order_number}: {new_status.replace('_', ' ').title()}. {status_messages.get(new_status, '')}"
            sms_notification = await self.create_notification(
                user_id=customer.id,
                order_id=order_id,
                type="sms",
                subject=None,
                message=sms_message
            )
            await self.send_notification(sms_notification.id)

    async def notify_agent_assignment(self, order_id: UUID, agent_id: UUID):
        """Notify agent of new assignment"""
        from app.models import Agent
        from app.services.order import OrderService
        order_service = OrderService(self.db)
        order = await order_service.get_order(order_id)

        result = await self.db.execute(
            select(Agent).options(selectinload(Agent.user)).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent or not agent.user:
            return

        subject = f"New Delivery Assignment - {order.order_number}"
        message = f"""
        <h2>New Delivery Assignment</h2>
        <p>Order: <strong>{order.order_number}</strong></p>
        <p>Pickup: {order.pickup_address}, {order.pickup_pincode}</p>
        <p>Drop: {order.drop_address}, {order.drop_pincode}</p>
        <p><a href="{settings.FRONTEND_URL}/agent/orders/{order.id}">View details</a></p>
        """

        email_notification = await self.create_notification(
            user_id=agent.user.id,
            order_id=order_id,
            type="email",
            subject=subject,
            message=message
        )
        await self.send_notification(email_notification.id)

        if agent.user.phone:
            sms_message = f"New delivery assigned: {order.order_number}. Pickup: {order.pickup_pincode}, Drop: {order.drop_pincode}"
            sms_notification = await self.create_notification(
                user_id=agent.user.id,
                order_id=order_id,
                type="sms",
                subject=None,
                message=sms_message
            )
            await self.send_notification(sms_notification.id)


async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)
