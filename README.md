WasteWise Nigeria

A community waste management and recycling platform that connects households with waste collectors, enables illegal dump reporting, and provides educational resources on responsible waste disposal.


Tech Stack
| Language | Python 3.10+ |
| Framework | Flask 3.0 |
| Database | SQLite (via SQLAlchemy ORM) |
| Authentication | JWT (Flask-JWT-Extended) |
| File Uploads | Local filesystem (`uploads/` folder) |
| Cross-Origin | Flask-CORS |


Project Structure


wastewise/
├── run.py                        
├── seed.py                       
├── requirements.txt              
├── .env.example                  
├── .gitignore
└── app/
    ├── __init__.py               
    ├── extensions.py             
    ├── models/
    │   └── __init__.py           
    ├── routes/
    │   ├── auth.py               
    │   ├── collections.py        
    │   ├── centers.py            
    │   ├── dumps.py              
    │   ├── resources.py          
    │   ├── announcements.py     
    │   ├── notifications.py      
    │   └── admin.py              
    └── utils/
        └── __init__.py          

Setup & Installation

1. Clone the repository

git clone <your-repo-url>
cd wastewise-flask


2. Create and activate a virtual environment
python -m venv venv

#Mac/Linux
source venv/bin/activate

#Windows
venv\Scripts\activate


3. Install dependencies
pip install -r requirements.txt


4. Configure environment variables

cp .env.example .env


Open `.env` and set your values:

SECRET_KEY=any-random-string-you-choose
JWT_SECRET_KEY=another-random-string-you-choose
DATABASE_URL=sqlite:///wastewise.db
UPLOAD_FOLDER=uploads


#5. Start the server
python run.py


The server starts at http://localhost:5000. The database file (`wastewise.db`) and `uploads/` folder are created automatically on first run.

6. Seed the database with test data
python seed.py



Test Accounts (after seeding)

| Role | Email | Password |
|---|---|---|
| Super Admin | admin@wastewise.ng | Admin1234! |
| Community Admin | community@wastewise.ng | Admin1234! |
| Collector | collector@wastewise.ng | Collect1234! |
| Household | household@wastewise.ng | House1234! |


User Roles

| Role | Permissions |
|---|---|
| `HOUSEHOLD` | Request collections, report dumps, read resources & announcements, earn points |
| `COLLECTOR` | View & accept requests in their LGA, update collection status |
| `COMMUNITY_ADMIN` | View collections & dumps in their LGA, post announcements, resolve dump reports |
| `SUPER_ADMIN` | Full access — manage users, recycling centers, resources, analytics |



API Overview

All protected endpoints require:
Authorization: Bearer <token>

| Group | Base URL | Auth Required |
|---|---|---|
| Auth | `/api/auth` | Some |
| Collections | `/api/collections` | Yes |
| Recycling Centers | `/api/recycling-centers` | Some |
| Dump Reports | `/api/dump-reports` | Yes |
| Resources | `/api/resources` | Some |
| Announcements | `/api/announcements` | Yes |
| Notifications | `/api/notifications` | Yes |
| Admin | `/api/admin` | Yes (Admin only) |



Health Check
GET /health

Returns `{ "status": "OK", "app": "WasteWise Nigeria" }` — no auth required.


Image Uploads

Send as `multipart/form-data`
Field name: `images` (multiple) or `image` / `avatar` (single)
Accepted formats: JPG, PNG, WEBP
Max size: 5MB per file
Images served at: `http://localhost:5000/uploads/<filename>`



Points System

Households automatically earn +10 points when a collection request is marked as `COLLECTED` by the collector.
Points are stored on the user profile.