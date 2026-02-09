from fastapi import Depends, HTTPException, status, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

from data.tables import get_db, WalkingSessions, ActivityType
from auth import get_current_user, Users
from routers import contact, payment
from config import get_settings

settings = get_settings()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contact.router)
app.include_router(payment.router)

class SessionStartRequest(BaseModel):
    is_baseline: bool = False
    notes: Optional[str] = None


class SessionStartResponse(BaseModel):
    session_id: int
    start_time: datetime
    status: str


@app.post("/api/sessions/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: SessionStartRequest,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    POST /api/sessions/start 
    """
    try:
        # Создаем новую сессию
        session = WalkingSessions(
            user_id=current_user.id,
            start_time=datetime.now(timezone.utc),
            is_baseline=request.is_baseline,
            is_processed=False,
            notes=request.notes,
            activity_type=ActivityType.NONE  # Default activity type
        )
        
        # Сохраняем в БД
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        # Возвращаем ответ
        return SessionStartResponse(
            session_id=session.id,
            start_time=session.start_time,
            status="recording"
        )
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании сессии: {str(e)}"
        )
