from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api import auth, incidents, departments, command_center, websocket, notifications
from app.models.department import Department
from app.utils.enums import DepartmentName

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic AI-powered campus emergency response platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        departments_data = [
            {"name": DepartmentName.MEDICAL, "description": "Campus Medical Responders"},
            {"name": DepartmentName.SECURITY, "description": "Campus Security Team"},
            {"name": DepartmentName.TRANSPORT, "description": "Campus Transportation and Ambulances"},
            {"name": DepartmentName.FACILITIES, "description": "Facilities and Maintenance"},
            {"name": DepartmentName.COMMUNICATION, "description": "Campus Communications"}
        ]
        for d_data in departments_data:
            dept = db.query(Department).filter(Department.name == d_data["name"]).first()
            if not dept:
                dept = Department(name=d_data["name"], description=d_data["description"])
                db.add(dept)
        db.commit()
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"http://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(incidents.router, prefix=f"{settings.API_V1_STR}/incidents", tags=["incidents"])
app.include_router(departments.router, prefix=f"{settings.API_V1_STR}/department", tags=["departments"])
app.include_router(command_center.router, prefix=f"{settings.API_V1_STR}/command-center", tags=["command-center"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

@app.get("/")
def root():
    return {"message": "Welcome to CampusResQ AI API", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

