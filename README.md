# 🚨 CampusResQ AI

### AI-Powered Campus Emergency Response & Safety Platform

> **Report. Analyze. Respond. Protect.**

CampusResQ AI is an intelligent **campus emergency management system** that helps students and staff report emergencies and enables responders, departments, and administrators to manage those emergencies efficiently.

The platform uses **Agentic AI** to analyze emergency reports, classify incidents, determine priority, detect potentially fraudulent reports, provide safety instructions, translate AI responses, and support emergency response coordination.

---

## 📌 1. Problem Statement

In a campus emergency, users may face several difficulties:

* They may not know which department to contact.
* Emergency details may not be communicated clearly.
* Response teams may take time to understand the situation.
* False or duplicate reports can create unnecessary workload.
* Users may need immediate safety instructions.
* Different users may prefer different languages.
* Responders need real-time information about incidents.

### 💡 Our Solution

CampusResQ AI brings all these activities into **one centralized platform**.

Instead of simply receiving an emergency report, the system can:

```text
Report Emergency
       ↓
Analyze Incident
       ↓
Classify Emergency
       ↓
Determine Priority
       ↓
Detect Fraud
       ↓
Provide Safety Instructions
       ↓
Assign Department / Responder
       ↓
Track Response
       ↓
Resolve Emergency
```

---

# 🎯 2. Main Objective

The main objective of CampusResQ AI is to **reduce emergency response time and improve campus safety using Agentic AI**.

The system connects:

* 🎓 Students
* 🧑‍🚒 Responders
* 🏢 Departments
* 👨‍💼 Administrators

through a single emergency-response platform.

---

# ✨ 3. Main Features

## 🚨 Emergency Reporting

Students can report an emergency by providing:

* Emergency description
* Location
* Category hint
* Evidence such as image, audio, or video
* SOS information
* Voice transcript when applicable

Example:

```text
What happened?
"Student injured near the laboratory."

Location:
Science Block

Emergency Type:
Medical
```

---

## 🤖 AI Incident Classification

The AI analyzes the emergency description and determines:

* Emergency category
* Responsible department
* Priority
* Confidence score
* Reason for classification
* Safety instructions

### Example

```text
Input:
"Smoke is coming from the electrical room."

AI Analysis:

Category    → Electrical / Fire
Department  → Fire Safety
Priority    → Critical
Confidence  → High

Safety:
Move away from the affected area
and follow evacuation instructions.
```

The backend contains an AI orchestration module in:

```text
backend/agents.py
```

It uses an LLM integration and also includes a **rule-based fallback** if the LLM is unavailable.

---

# ⚡ 4. Priority Levels

Every emergency can have one of four priority levels:

| Priority    | Meaning                                    |
| ----------- | ------------------------------------------ |
| 🟢 Low      | Minor issue requiring attention            |
| 🟡 Medium   | Situation needs timely response            |
| 🟠 High     | Serious situation requiring quick response |
| 🔴 Critical | Immediate emergency response required      |

The backend defines these priorities in `backend/models.py`.

---

# 🏢 5. Department Assignment

The system supports the following departments:

| Department       | Example                          |
| ---------------- | -------------------------------- |
| 🏥 Medical       | Injuries and medical emergencies |
| 🔥 Fire Safety   | Fire, smoke and fire hazards     |
| 🛡️ Security     | Security and safety incidents    |
| ⚡ Electrical     | Electrical problems              |
| 🏗️ Construction | Construction-related hazards     |
| 🏢 Facilities    | Campus facility problems         |
| 🌱 Environmental | Environmental incidents          |
| 🚌 Transport     | Transport-related incidents      |

The AI can recommend the appropriate department based on the emergency description.

---

# 🔍 6. AI Fraud Detection

CampusResQ AI includes a fraud-analysis capability.

The system can analyze reports for potentially suspicious activity, including:

* Duplicate reports
* Suspicious descriptions
* Repeated submissions
* Possible prank reports
* Unusual reporting patterns

The result includes:

```text
Risk Score
Risk Level
Reasons
Recommended Action
```

Fraud levels supported by the backend are:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

---

# 🛡️ 7. AI Safety Assistant

The system includes an AI assistant that can provide safety guidance to users.

For example, if a user reports a fire, the assistant can provide instructions such as:

```text
1. Move away from the affected area.
2. Follow campus evacuation instructions.
3. Avoid dangerous areas.
4. Move to a safe location.
5. Wait for emergency responders.
```

The assistant can also use the incident context when generating its response.

---

# 🌐 8. Multilingual Support

CampusResQ AI includes localization functionality.

The frontend contains:

```text
frontend/src/lib/i18n.js
```

The AI backend also contains translation functionality for AI analysis.

The project is designed to support multiple languages, including:

* English
* Hindi
* Telugu
* Tamil
* Kannada

---

# 🆘 9. SOS & Voice SOS

CampusResQ AI includes dedicated emergency assistance features.

### SOS

The SOS feature allows a user to quickly raise an emergency request.

### Voice SOS

The application also includes voice-based SOS functionality.

Frontend components:

```text
frontend/src/components/SOSButton.jsx
frontend/src/components/VoiceSOSButton.jsx
```

Backend endpoint:

```text
POST /api/voice/sos
```

SOS incidents are handled with high urgency.

---

# 🗺️ 10. Live Emergency Map

The application includes a live map component:

```text
frontend/src/components/LiveMap.jsx
```

The project uses:

* Leaflet
* React Leaflet
* Leaflet Heatmap

The map functionality helps visualize emergency locations and supports better situational awareness.

The backend also calculates geographical distance and responder ETA information.

---

# 📡 11. Real-Time Updates

CampusResQ AI supports real-time communication using **WebSockets**.

The backend maintains WebSocket connections for users and can send:

* Incident updates
* Notifications
* Priority information
* Emergency status changes

Frontend WebSocket functionality is implemented in:

```text
frontend/src/lib/ws.js
```

---

# 🔔 12. Notifications

The platform supports notifications for emergency events.

Notifications can be delivered through:

* In-app notifications
* WebSocket updates
* Web Push
* Email
* SMS

Relevant backend files include:

```text
backend/emailer.py
backend/sms.py
```

The project also contains:

```text
frontend/src/lib/push.js
```

for web push functionality.

---

# 📶 13. Offline Support

CampusResQ AI includes an offline synchronization mechanism.

If an operation needs to be queued while the application is offline, it can be stored locally and synchronized later.

The frontend contains an offline queue in:

```text
frontend/src/lib/api.js
```

The backend provides:

```text
POST /api/sync/queue
```

There is also an offline status component:

```text
frontend/src/components/OfflineIndicator.jsx
```

---

# 👥 14. User Roles

The system supports five roles.

```text
student
responder
dept_personnel
dept_admin
head_admin
```

---

## 🎓 Student

Students can:

* Register and log in
* Report emergencies
* Trigger SOS
* View emergency details
* View notifications
* Chat with the AI assistant
* Manage their profile

Main frontend pages:

```text
StudentDashboard.jsx
ReportEmergency.jsx
EmergencyDetail.jsx
Notifications.jsx
AssistantChat.jsx
Profile.jsx
```

---

## 🧑‍🚒 Responder

Responders can:

* View assigned emergencies
* Accept incidents
* Reject incidents
* Update emergency status
* Update their location
* Mark response progress
* Complete emergency response
* Manage availability

Main page:

```text
ResponderDashboard.jsx
```

---

## 🏢 Department Personnel / Department Admin

Department users can manage incidents assigned to their department.

Main page:

```text
DepartmentDashboard.jsx
```

Department administrators also have access to additional management functionality.

---

## 👨‍💼 Head Administrator

The head administrator has access to the command center and administrative functions.

Admin functionality includes:

* Incident monitoring
* Fraud monitoring
* Responder management
* Audit logs
* Teams
* Heatmaps
* Incident replay
* AI agent information
* Announcements
* System metrics

---

# 🧠 15. Agentic AI Workflow

The AI system is organized around specialized functions.

```text
                    Emergency Report
                           │
                           ▼
                ┌─────────────────────┐
                │ Classification Agent│
                └──────────┬──────────┘
                           │
                           ▼
                Category + Department
                           │
                           ▼
                ┌─────────────────────┐
                │  Priority Analysis  │
                └──────────┬──────────┘
                           │
                           ▼
                     Priority Level
                           │
                           ▼
                ┌─────────────────────┐
                │  Fraud Detection    │
                └──────────┬──────────┘
                           │
                           ▼
                     Risk Analysis
                           │
                           ▼
                ┌─────────────────────┐
                │  Safety Assistant   │
                └──────────┬──────────┘
                           │
                           ▼
                  Safety Instructions
                           │
                           ▼
                Department / Responder
                           │
                           ▼
                    Response Tracking
                           │
                           ▼
                       Resolved
```

The main AI functionality is implemented in:

```text
backend/agents.py
```

---

# 🏗️ 16. System Architecture

```text
                    ┌──────────────────┐
                    │ Student / Staff  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ React Frontend   │
                    │   Web Interface  │
                    └────────┬─────────┘
                             │
                        REST / WS
                             │
                             ▼
                    ┌──────────────────┐
                    │ FastAPI Backend  │
                    │    Python        │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
     AI Agents           Authentication     Notifications
          │                  │                  │
          │                  │          ┌───────┼───────┐
          │                  │          ▼       ▼       ▼
          │                  │        Push    Email    SMS
          │                  │
          └──────────┬───────┘
                     ▼
              ┌───────────────┐
              │   MongoDB     │
              └───────┬───────┘
                      │
                      ▼
             Responders / Admin
```

---

# 🛠️ 17. Technology Stack

## Frontend

* React 19
* JavaScript
* React Router
* Axios
* Tailwind CSS
* Framer Motion
* Leaflet
* React Leaflet
* Leaflet Heatmap
* Recharts
* Lucide React
* React Hook Form
* Zod
* Sonner

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* Motor
* PyMongo

## Database

* MongoDB

## AI

* Emergent LLM integration
* Claude Sonnet 4.6 integration through the project AI layer
* AI incident classification
* AI fraud analysis
* AI safety assistant
* AI translation

## Communication

* WebSockets
* Web Push
* Email
* SMS
* Twilio

---

# 📂 18. Project Structure

```text
Agentic-main/
│
├── backend/
│   ├── agents.py          # AI agent logic
│   ├── auth.py            # Authentication & authorization
│   ├── emailer.py         # Email notifications
│   ├── models.py          # Pydantic models & enums
│   ├── server.py          # FastAPI application & API routes
│   ├── sms.py             # SMS functionality
│   ├── requirements.txt   # Python dependencies
│   └── pytest.ini         # Backend test configuration
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── constants/     # Application constants
│   │   ├── contexts/      # React contexts
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # API, WebSocket, push & utilities
│   │   └── pages/         # Application pages
│   │
│   ├── package.json       # Frontend dependencies
│   ├── craco.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── memory/
│   └── PRD.md             # Product requirements
│
├── tests/
├── test_reports/
├── design_guidelines.json
├── app.code-workspace
├── .gitignore
└── README.md
```

---

# 🚀 19. Installation

## Prerequisites

Install the following before running the project:

* Python 3
* Node.js
* npm
* MongoDB
* Git

---

# ⚙️ 20. Backend Setup

Open Terminal and clone the project:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Agentic-main
```

Go to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate the environment:

### macOS / Linux

```bash
source venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔐 21. Backend Environment Variables

The backend reads environment variables from:

```text
backend/.env
```

Create the file:

```bash
touch .env
```

Add the required configuration.

Example:

```env
MONGO_URL=your_mongodb_connection_string
DB_NAME=campusresq

JWT_SECRET=your_secure_secret
JWT_ALG=HS256

EMERGENT_LLM_KEY=your_llm_key

CORS_ORIGINS=http://localhost:3000

VAPID_PUBLIC=your_vapid_public_key
VAPID_PRIVATE=your_vapid_private_key
VAPID_SUBJECT=mailto:admin@example.com

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM=your_twilio_phone_number

EMERGENT_EMAIL_KEY=your_email_key
EMAIL_FROM_NAME=CampusResQ AI
EMAIL_REPLY_TO=your_email_address

WEBHOOK_CRON_SECRET=your_webhook_secret
```

> ⚠️ **Do not upload `.env` to GitHub.**

Your `.gitignore` already contains rules for environment files and credentials.

---

# ▶️ 22. Start the Backend

From the `backend` directory:

```bash
uvicorn server:app --reload
```

The FastAPI backend will start using Uvicorn.

You can also access the FastAPI documentation from the server's `/docs` endpoint.

---

# 💻 23. Frontend Setup

Open a **new Terminal window**.

Go to the frontend:

```bash
cd Agentic-main/frontend
```

Install dependencies:

```bash
npm install
```

Start the React application:

```bash
npm start
```

The frontend normally runs at:

```text
http://localhost:3000
```

---

# 🔗 24. Frontend–Backend Connection

The frontend obtains the backend URL from:

```text
REACT_APP_BACKEND_URL
```

The API configuration is located in:

```text
frontend/src/lib/api.js
```

The frontend creates the API base URL as:

```text
REACT_APP_BACKEND_URL + /api
```

Therefore, make sure the frontend environment is configured with the correct backend URL.

---

# 🔌 25. Important API Endpoints

The backend uses the `/api` prefix.

## Authentication

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

## Emergency Management

```text
POST /api/emergencies
GET  /api/emergencies
GET  /api/emergencies/{incident_id}
```

## Responder Actions

```text
POST /api/emergencies/{incident_id}/accept
POST /api/emergencies/{incident_id}/reject
POST /api/emergencies/{incident_id}/status
POST /api/emergencies/{incident_id}/location
POST /api/emergencies/{incident_id}/responder-complete
```

## AI Assistant

```text
POST /api/ai/assistant
```

## Voice SOS

```text
POST /api/voice/sos
```

## Notifications

```text
GET  /api/notifications
POST /api/notifications/{nid}/read
POST /api/notifications/read-all
```

## Push Notifications

```text
GET  /api/push/vapid-public
POST /api/push/subscribe
POST /api/push/unsubscribe
```

## Administration

```text
GET /api/admin/incidents
GET /api/admin/fraud
GET /api/admin/heatmap
GET /api/admin/responders
GET /api/admin/audit
GET /api/admin/metrics
```

---

# 🔄 26. Complete Emergency Workflow

### Step 1 — User Reports

The student enters:

```text
Emergency description
Location
Category
Evidence
```

---

### Step 2 — Backend Receives the Report

The request is sent to:

```text
POST /api/emergencies
```

---

### Step 3 — AI Analyzes the Incident

The AI determines:

```text
Category
Department
Priority
Confidence
Reason
Safety Instructions
```

---

### Step 4 — Fraud Analysis

The system checks whether the report appears suspicious.

```text
Risk Score
Risk Level
Reasons
Recommended Action
```

---

### Step 5 — Department Assignment

The incident is routed toward the appropriate department and responder workflow.

---

### Step 6 — Responder Accepts

A responder can accept or reject the emergency.

---

### Step 7 — Response Tracking

The responder can update:

```text
Accepted
En Route
Arrived
Resolved
```

The system can also maintain responder location and calculate distance/ETA information.

---

### Step 8 — Emergency Resolution

After the response is completed, the incident is marked as resolved.

The incident timeline keeps track of important events.

---

# 📊 27. Incident Status Flow

The backend supports detailed incident states:

```text
SUBMITTED
    ↓
ANALYZING
    ↓
CLASSIFIED
    ↓
FRAUD_REVIEW
    ↓
ASSIGNING
    ↓
WAITING_FOR_ACCEPTANCE
    ↓
ASSIGNED
    ↓
ACCEPTED
    ↓
EN_ROUTE
    ↓
ARRIVED
    ↓
RESOLVED
```

Additional states include:

```text
RESOLUTION_PENDING
REOPENED
CANCELLED
ESCALATED
```

This allows the system to track the emergency throughout its complete lifecycle.

---

# 🔒 28. Authentication & Security

CampusResQ AI includes authentication and authorization features.

The backend uses:

* Password hashing
* JWT authentication
* Role-based access control
* Protected API endpoints
* Password-strength validation
* Environment-based secrets

The system validates different registration formats for students and staff.

---

# 🧪 29. Testing

Backend testing is configured using:

```text
pytest
```

Run tests with:

```bash
pytest
```

The backend also includes development tools for:

```text
Black
Flake8
isort
mypy
```

---

# 👨‍💻 30. What Each Team Member Should Know

If you are joining this project, start here:

### Frontend Developer

Work mainly inside:

```text
frontend/src/
```

Important folders:

```text
components/
pages/
contexts/
hooks/
lib/
```

---

### Backend Developer

Work mainly inside:

```text
backend/
```

Important files:

```text
server.py
models.py
auth.py
```

---

### AI Developer

Work mainly inside:

```text
backend/agents.py
```

This contains the AI classification, fraud analysis, assistant, translation, notification-related AI helpers, and fallback logic.

---

### UI Developer

Main areas:

```text
frontend/src/components/
frontend/src/pages/
frontend/src/App.css
frontend/src/index.css
```

---

### Database / Backend Developer

Main areas:

```text
backend/server.py
backend/models.py
```

The backend uses MongoDB through Motor/PyMongo.

---

# 🏆 31. Why CampusResQ AI Is Different

Most emergency reporting systems only perform:

```text
Report → Notify
```

CampusResQ AI aims to provide:

```text
Report
  ↓
Understand
  ↓
Classify
  ↓
Prioritize
  ↓
Check for Fraud
  ↓
Give Safety Instructions
  ↓
Assign
  ↓
Track
  ↓
Resolve
```

This makes the project an **AI-assisted emergency response platform**, rather than just an emergency reporting form.

---

# 📈 32. Future Improvements

Possible future enhancements include:

* 📱 Native Android/iOS application
* 📍 More advanced GPS tracking
* 🧑‍🚒 Dedicated responder mobile application
* 🏥 Hospital integration
* 🚓 External emergency-service integration
* 📞 Direct emergency calling
* 📊 Advanced emergency analytics
* 🤖 Additional specialized AI agents
* ☁️ Production cloud deployment
* 📡 Improved offline communication
* 🔥 Predictive emergency-risk analysis

---

# 🎓 33. Hackathon Project Summary

**CampusResQ AI** demonstrates how **Agentic AI can improve emergency management in educational institutions**.

The system combines:

```text
Artificial Intelligence
        +
Emergency Management
        +
Real-Time Communication
        +
Location Awareness
        +
Fraud Detection
        +
Multilingual Assistance
        +
Role-Based Management
```

to create a smarter and more coordinated campus safety ecosystem.

---

# 👥 34. Team

## CampusResQ AI

**Project Type:** Agentic AI / Smart Campus / Emergency Response

**Goal:**
To make campus emergency reporting and response **faster, smarter, and safer**.

---

# 📜 35. License

This project is developed for **educational, research, and hackathon purposes**.

---

## ❤️ CampusResQ AI

> **One platform. One connected response. A safer campus.**
