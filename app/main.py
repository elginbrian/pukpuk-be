from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .infrastructure.config.settings import Settings
from .infrastructure.database.database import init_database, close_database, is_database_available, get_database
from .application.handler.routes.forecasting import router as forecasting_router
from .application.handler.routes.ai_insight import router as ai_insight_router
from .application.handler.routes.route_optimization import router as route_optimization_router
from .application.handler.routes.maps import router as maps_router
from .application.handler.routes.demand_heatmap import router as demand_heatmap_router
from .application.handler.routes.health import router as health_router

# Initialize settings
settings = Settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://pukpuk-id.vercel.app", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(forecasting_router)
app.include_router(ai_insight_router)
app.include_router(route_optimization_router)
app.include_router(demand_heatmap_router)
app.include_router(health_router)

@app.on_event("startup")
async def startup_event():
    await init_database()
    
    if is_database_available():
        from .infrastructure.utils.seed_service import SeedService
        db = get_database()
        seed_service = SeedService(db)
        await seed_service.seed_all_data()

@app.on_event("shutdown")
async def shutdown_event():
    await close_database()
    
    try:
        from .application.handler.routes.route_optimization import cleanup_http_client
        await cleanup_http_client()
    except Exception as e:
        print(f"Error closing HTTP client: {e}")

@app.get("/")
async def root():
    return {"message": "Welcome to PukPuk Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)