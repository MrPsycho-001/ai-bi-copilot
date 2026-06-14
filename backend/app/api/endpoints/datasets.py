import os
import shutil
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import Dataset

router = APIRouter()

UPLOAD_DIR = "storage/datasets"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    allowed_extensions = [".csv", ".xlsx", ".xls", ".json"]
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"File type {ext} not permitted."
        )
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)
        
    df = None
    try:
        if ext == '.csv':
            df = pd.read_csv(file_path, nrows=5)
        elif ext in ['.xlsx', '.xls']:
            try:
                df = pd.read_excel(file_path, nrows=5)
            except Exception:
                df = pd.read_csv(file_path, nrows=5)
        elif ext == '.json':
            df = pd.read_json(file_path)
            
        if df is None or df.empty:
            raise ValueError("The parsed file contains no readable data rows.")
            
        columns_map = {col: str(dtype) for col, dtype in df.dtypes.items()}
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Data structure validation failed: {str(e)}"
        )

    # Added user_id=1 to satisfy the database's NOT NULL constraint!
    new_dataset = Dataset(
        filename=file.filename,
        storage_path=file_path,
        file_size_bytes=file_size,
        schema_metadata=columns_map,
        user_id=1
    )
    db.add(new_dataset)
    await db.commit()
    await db.refresh(new_dataset)
    
    return {
        "dataset_id": new_dataset.id,
        "filename": new_dataset.filename,
        "detected_columns": columns_map
    }
