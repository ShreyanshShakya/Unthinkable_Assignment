from fastapi import APIRouter

from app.api.admin_agents import router as admin_agents_router
from app.api.admin_rates import router as admin_rates_router
from app.api.admin_zones import router as admin_zones_router
from app.api.agents import router as agents_router
from app.api.auth import router as auth_router
from app.api.failed_deliveries import router as failed_deliveries_router
from app.api.orders import router as orders_router
from app.api.pricing import router as pricing_router
from app.api.zone_detection import router as zone_detection_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(admin_agents_router)
api_router.include_router(admin_zones_router)
api_router.include_router(admin_rates_router)
api_router.include_router(zone_detection_router)
api_router.include_router(pricing_router)
api_router.include_router(orders_router)
api_router.include_router(agents_router)
api_router.include_router(failed_deliveries_router)
