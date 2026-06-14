from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.models import Dataset
from app.agents.bi_agent import bi_agent_executor

router = APIRouter()

# 1. We added a history list to the expected incoming payload
class ChatRequest(BaseModel):
    dataset_id: int
    message: str
    history: List[Dict[str, Any]] = []

@router.post("/chat")
async def chat_with_dataset(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dataset).filter(Dataset.id == payload.dataset_id))
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target dataset metadata not found."
        )

    # 2. We inject the history into the AI's initial state
    initial_state = {
        "user_query": payload.message,
        "chat_history": payload.history,
        "dataset_path": dataset.storage_path,
        "schema_metadata": dataset.schema_metadata or {},
        "extracted_metrics": {},
        "final_response": "",
        "next_step": ""
    }

    try:
        output_state = await bi_agent_executor.ainvoke(initial_state)
        
        return {
            "status": "success",
            "user_query": payload.message,
            "response": output_state["final_response"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent coordination runtime error: {str(e)}"
        )
