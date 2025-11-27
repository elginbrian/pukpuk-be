from fastapi import FastAPI
from .infrastructure.config.settings import Settings
from .application.handler.routes.forecasting import router as forecasting_router

# Initialize settings
settings = Settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug
)

# Include routers
app.include_router(forecasting_router)

@app.get("/")
async def root():
    return {"message": "Welcome to PukPuk Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)