from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .infrastructure.config.settings import Settings
from .infrastructure.database.database import init_database, close_database, seed_database
from .application.handler.routes.forecasting import router as forecasting_router
from .application.handler.routes.ai_insight import router as ai_insight_router
from .application.handler.routes.route_optimization import router as route_optimization_router

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

@app.on_event("startup")
async def startup_event():
    await init_database()
    await seed_database()
    from .infrastructure.utils.seed_service import SeedService
    seed_service = SeedService()
    await seed_service.seed_all_data()

@app.on_event("shutdown")
async def shutdown_event():
    await close_database()

@app.get("/")
async def root():
    return {"message": "Welcome to PukPuk Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)