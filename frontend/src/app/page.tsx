export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Last Mile Delivery Tracker
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Backend API is running. Frontend coming soon.
        </p>
        <a
          href="/api/docs"
          className="btn-primary"
          target="_blank"
          rel="noopener noreferrer"
        >
          View API Docs
        </a>
      </div>
    </main>
  );
}