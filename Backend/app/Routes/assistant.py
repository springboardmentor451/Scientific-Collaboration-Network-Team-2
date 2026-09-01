from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.Schemas.assistant import AssistantMessage, AssistantResponse
from app.Services.assistant import ask_ollama, build_context, immediate_help, record_answer, request_lock
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/assistant", tags=["SCNA Assistant"])


@router.post("/chat", response_model=AssistantResponse)
def chat(data: AssistantMessage, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Please enter a question.")
    direct_answer = immediate_help(message, user)
    if direct_answer:
        return {"answer": direct_answer, "source": "SCNA Assistant guidance", "link": None}
    lock = request_lock(user.id)
    if not lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="The assistant is already responding. Please wait.")
    try:
        context, _topic, link = build_context(db, user, message)
        exact_answer = record_answer(context, _topic, message)
        if exact_answer:
            return {"answer": exact_answer, "source": "Real permitted SCNA database records", "link": link}
        try:
            answer = ask_ollama(message, context)
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail="The assistant is temporarily unavailable. Please try again.") from error
        return {"answer": answer, "source": "Local Ollama model using permitted SCNA records", "link": link}
    finally:
        lock.release()
