from fastapi import APIRouter
from typing import Dict, Any
import psutil
import os
from ....infrastructure.database.database import is_database_available

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "pukpuk-backend",
        "database": "connected" if is_database_available() else "disconnected"
    }

@router.get("/metrics")
async def health_metrics() -> Dict[str, Any]:
    """Detailed health metrics including resource usage."""
    process = psutil.Process(os.getpid())
    
    try:
        num_fds = process.num_fds()
    except AttributeError:
        num_fds = process.num_handles() if hasattr(process, 'num_handles') else 0
    
    mem_info = process.memory_info()
    
    try:
        open_files = len(process.open_files())
    except:
        open_files = 0
    
    try:
        connections = len(process.connections())
    except:
        connections = 0
    
    return {
        "status": "healthy",
        "database": "connected" if is_database_available() else "disconnected",
        "resources": {
            "file_descriptors": num_fds,
            "open_files": open_files,
            "connections": connections,
            "memory_mb": round(mem_info.rss / 1024 / 1024, 2),
            "memory_percent": round(process.memory_percent(), 2),
            "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
            "threads": process.num_threads()
        }
    }
