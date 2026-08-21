from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.utils.enums import NotificationType

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(self, user_id: str, type: NotificationType, title: str, message: str, incident_id: str = None):
        notif = Notification(
            user_id=user_id,
            incident_id=incident_id,
            type=type,
            title=title,
            message=message
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif
