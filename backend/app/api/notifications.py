from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.schemas.notification import NotificationResponse
from app.models.user import User
from app.models.notification import Notification

router = APIRouter()

@router.get("", response_model=List[NotificationResponse])
def get_notifications(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()

@router.post("/{notification_id}/read")
def read_notification(notification_id: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "success"}

@router.post("/read-all")
def read_all_notifications(db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    db.query(Notification).filter(Notification.user_id == current_user.id).update({"is_read": True})
    db.commit()
    return {"status": "success"}
