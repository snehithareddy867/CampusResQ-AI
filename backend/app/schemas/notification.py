from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.utils.enums import NotificationType

class NotificationResponse(BaseModel):
    id: str
    incident_id: Optional[str] = None
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
