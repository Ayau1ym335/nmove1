
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.data.tables import get_db
from app.routers.schemas import ChatRequest, ChatResponse, ChatSessionResponse
from ai.chat import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/start", response_model=ChatSessionResponse)
def start_chat_session(
    user_id: int,
    report_id: int = None,
    db: Session = Depends(get_db)
):
    chat_service = ChatService(db)
    session = chat_service.get_or_create_session(user_id, report_id)
    return session


@router.post("/message", response_model=ChatResponse)
def send_chat_message(
    session_id: int,
    message: str,
    db: Session = Depends(get_db)
):
    chat_service = ChatService(db)
    
    try:
        response_text = chat_service.send_message(session_id, message)
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            timestamp=datetime.utcnow()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )


@router.get("/{session_id}/history")
def get_chat_history(session_id: int, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    try:
        history = chat_service.get_chat_history(session_id)
        return {"session_id": session_id, "history": history}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{session_id}/end")
def end_chat_session(session_id: int, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    chat_service.end_session(session_id)
from datetime import datetime