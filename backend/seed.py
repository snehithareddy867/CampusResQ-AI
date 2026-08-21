import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.department import Department
from app.models.user import User
from app.utils.enums import DepartmentName
from app.core.security import get_password_hash

def seed_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("Seeding departments...")
    departments_data = [
        {"name": DepartmentName.MEDICAL, "description": "Campus Medical Responders"},
        {"name": DepartmentName.SECURITY, "description": "Campus Security Team"},
        {"name": DepartmentName.TRANSPORT, "description": "Campus Transportation and Ambulances"},
        {"name": DepartmentName.FACILITIES, "description": "Facilities and Maintenance"},
        {"name": DepartmentName.COMMUNICATION, "description": "Campus Communications"}
    ]
    
    dept_map = {}
    for d_data in departments_data:
        dept = db.query(Department).filter(Department.name == d_data["name"]).first()
        if not dept:
            dept = Department(name=d_data["name"], description=d_data["description"])
            db.add(dept)
            db.commit()
            db.refresh(dept)
        dept_map[d_data["name"]] = dept

    print("Seeding users...")
    users_data = [
        {"email": "medical1@example.com", "name": "Dr. Sarah", "dept": DepartmentName.MEDICAL},
        {"email": "medical2@example.com", "name": "Nurse John", "dept": DepartmentName.MEDICAL},
        {"email": "security1@example.com", "name": "Officer Mike", "dept": DepartmentName.SECURITY},
        {"email": "security2@example.com", "name": "Officer Jane", "dept": DepartmentName.SECURITY},
        {"email": "transport1@example.com", "name": "Driver Tom", "dept": DepartmentName.TRANSPORT},
        {"email": "transport2@example.com", "name": "Driver Lucy", "dept": DepartmentName.TRANSPORT},
        {"email": "facilities1@example.com", "name": "Tech Bob", "dept": DepartmentName.FACILITIES},
        {"email": "facilities2@example.com", "name": "Tech Alice", "dept": DepartmentName.FACILITIES},
        {"email": "communication1@example.com", "name": "Comm Anna", "dept": DepartmentName.COMMUNICATION},
        {"email": "normaluser@example.com", "name": "Student Rahul", "dept": DepartmentName.NONE}
    ]
    
    for u_data in users_data:
        user = db.query(User).filter(User.email == u_data["email"]).first()
        if not user:
            dept_id = dept_map[u_data["dept"]].id if u_data["dept"] != DepartmentName.NONE else None
            user = User(
                email=u_data["email"],
                name=u_data["name"],
                campus_id=f"ID-{u_data['name'].replace(' ', '')}",
                hashed_password=get_password_hash("password123"),
                department_id=dept_id
            )
            db.add(user)
    
    db.commit()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_db()
