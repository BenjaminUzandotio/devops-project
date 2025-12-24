from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import time
import psutil
import os

from src.database import engine, Base, get_db
from src.models import UserDB
from src.schemas import UserCreate, UserResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="User API", version="1.0.0", lifespan=lifespan)

# --- BONUS: Middleware Monitoring ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# --- BONUS: Metrics Endpoint ---
@app.get("/metrics")
def get_metrics():
    process = psutil.Process(os.getpid())
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
        "status": "running"
    }

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    new_user = UserDB(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(UserDB).offset(skip).limit(limit).all()

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.email != db_user.email:
        if db.query(UserDB).filter(UserDB.email == user_update.email).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already taken")
    db_user.name = user_update.name
    db_user.email = user_update.email
    db_user.age = user_update.age
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return
