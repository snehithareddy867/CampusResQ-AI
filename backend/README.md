# CampusResQ AI Backend

An Agentic AI-powered campus emergency response and coordination platform.

## Overview
CampusResQ AI is not a simple CRUD application. It demonstrates an **Agentic AI workflow**:
1. User reports an emergency.
2. AI Orchestrator understands the incident, determines severity, and identifies required departments.
3. AI coordinates multi-agent response (Medical, Security, Transport, etc.).
4. The system updates live ETA and statuses.
5. The AI replans dynamically when conditions change.

## Architecture
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (via SQLAlchemy)
- **Auth**: JWT
- **Real-time**: WebSockets
- **AI Integration**: OpenAI (with Mock fallback)

## Installation & Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your values.
   *(Note: The system defaults to SQLite for easy local setup if DATABASE_URL is left as default SQLite URL or not provided)*

3. **Database Setup & Seeding**:
   ```bash
   python seed.py
   ```

4. **Run the Backend**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.
   Swagger Docs: `http://localhost:8000/docs`

## Demo Accounts
Passwords for all demo accounts are `password123`.

- **Medical**: medical1@example.com
- **Security**: security1@example.com
- **Transport**: transport1@example.com
- **Facilities**: facilities1@example.com
- **Communication**: communication1@example.com
- **Normal User (No Dept)**: normaluser@example.com

## Demo Scenario
1. Login as `normaluser@example.com`.
2. Report: "Student collapsed near library."
3. Wait for the Orchestrator to classify it as a CRITICAL MEDICAL incident and assign Medical + Security.
4. Login as `medical1@example.com`, check dashboard, accept and dispatch.
5. Trigger replan via API to see the AI dynamically update ETA and route.
6. Resolve the incident.
