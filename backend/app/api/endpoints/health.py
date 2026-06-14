from typing import Dict, Any
from fastapi import APIRouter

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def check_health() -> Dict[str, Any]:
    return {"status": "healthy", "version": "1.0.0", "services": {"api_layer": "operational"}}
