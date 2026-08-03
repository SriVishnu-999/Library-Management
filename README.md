Library Management REST API
A clean, OOP-driven RESTful backend for managing books, members, and borrow/return lifecycles — built with Flask and PostgreSQL.

What This Project Does
Libraries juggle three moving parts: what's on the shelf, who's borrowing, and what's overdue. This API models all three as first-class resources and exposes them over a consistent REST interface.

Problem	How this API solves it
Tracking inventory	books resource with full CRUD + availability state
Managing membership	members resource with validation and lookup
Knowing who has what	issues join table linking books ↔ members with timestamps
Catching late returns	SQL-driven overdue queries with date filters
Features
OOP module structure — models, services, and routes live in separate layers, not one giant file
Full CRUD on books, members, and issue/return records
Relational SQL — joins, filters, and constraints instead of app-side data stitching
⏰ Overdue tracking — query borrowers past their due date in a single request
Postman-verified — every endpoint tested end-to-end with a shareable collection
Consistent conventions — predictable request/response shapes and HTTP status codes
Architecture
        HTTP Client (Postman / Frontend)
                     │
                     ▼
        ┌────────────────────────┐
        │   Flask Route Layer    │  ← request parsing, status codes
        └───────────┬────────────┘
                    ▼
        ┌────────────────────────┐
        │    Service Layer       │  ← business rules (can this book be issued?)
        └───────────┬────────────┘
                    ▼
        ┌────────────────────────┐
        │  Data Access / Models  │  ← SQL, joins, constraints
        └───────────┬────────────┘
                    ▼
              PostgreSQL
Why layered? Business rules never touch SQL strings, and routes never contain logic. Swap the database or add a new interface without rewriting the core.

Project Structure
library-management-api/
├── app/
│   ├── __init__.py          # app factory + blueprint registration
│   ├── config.py            # env-driven configuration
│   ├── models/              # Book, Member, IssueRecord classes
│   ├── services/            # borrow/return rules, overdue logic
│   ├── routes/              # /books, /members, /issues blueprints
│   └── db/                  # connection pool + query helpers
├── sql/
│   └── schema.sql           # tables, keys, constraints
├── postman/
│   └── collection.json      # importable API collection
├── requirements.txt
└── README.md
Data Model
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│    books     │        │  issue_records   │        │   members    │
├──────────────┤        ├──────────────────┤        ├──────────────┤
│ id (PK)      │◄──────┤ book_id   (FK)   ├──────►│ id (PK)      │
│ title        │        │ member_id (FK)   │        │ name         │
│ author       │        │ issue_date       │        │ email UNIQUE │
│ isbn UNIQUE  │        │ due_date         │        │ phone        │
│ total_copies │        │ return_date NULL │        │ joined_on    │
│ available    │        │ status           │        │              │
└──────────────┘        └──────────────────┘        └──────────────┘
A NULL return_date + due_date < CURRENT_DATE = overdue. Simple, indexable, no ambiguity.

Getting Started
Prerequisites
Python 3.10+
PostgreSQL 13+
Installation
# 1. Clone
git clone https://github.com/<your-username>/library-management-api.git
cd library-management-api

# 2. Virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Database
createdb library_db
psql -d library_db -f sql/schema.sql

# 5. Environment
cp .env.example .env          # then fill in your credentials
.env template
DATABASE_URL=postgresql://user:password@localhost:5432/library_db
FLASK_ENV=development
SECRET_KEY=change-me
Run it
flask run
# http://127.0.0.1:5000
API Reference
Books
Method	Endpoint	Description
GET	/api/books	List all books (supports ?author= & ?available=true)
GET	/api/books/<id>	Fetch a single book
POST	/api/books	Add a new book
PUT	/api/books/<id>	Update book details
DELETE	/api/books/<id>	Remove a book
Method	Endpoint	Description
GET	/api/members	List all members
GET	/api/members/<id>	Member profile + active loans
POST	/api/members	Register a member
PUT	/api/members/<id>	Update member
DELETE	/api/members/<id>	Remove member
Method	Endpoint	Description
POST	/api/issues	Issue a book to a member
PATCH	/api/issues/<id>/return	Mark a book returned
GET	/api/issues/overdue	All overdue loans
GET	/api/members/<id>/history	Full borrow history
Example Requests
Issue a book

curl -X POST http://localhost:5000/api/issues \
  -H "Content-Type: application/json" \
  -d '{ "book_id": 12, "member_id": 4, "days": 14 }'
Response — 201 Created

{
  "success": true,
  "data": {
    "issue_id": 87,
    "book": "Clean Code",
    "member": "Aarav Sharma",
    "issue_date": "2026-08-03",
    "due_date": "2026-08-17",
    "status": "ISSUED"
  }
}
Error — 409 Conflict

{
  "success": false,
  "error": "NO_COPIES_AVAILABLE",
  "message": "All copies of 'Clean Code' are currently issued."
}
SQL Highlight — Overdue Report
SELECT  m.name,
        m.email,
        b.title,
        i.due_date,
        CURRENT_DATE - i.due_date AS days_overdue
FROM    issue_records i
JOIN    members m ON m.id = i.member_id
JOIN    books   b ON b.id = i.book_id
WHERE   i.return_date IS NULL
  AND   i.due_date < CURRENT_DATE
ORDER BY days_overdue DESC;
Postman
Open Postman → Import → select postman/collection.json
Set the base_url environment variable to http://localhost:5000
Run the collection top-to-bottom — requests are ordered so created IDs flow forward
Roadmap
 JWT authentication with librarian / member roles
 Fine calculation on overdue returns
 Reservation queue for unavailable titles
 Dockerised setup with docker compose up
 Swagger / OpenAPI docs
Contributing
Pull requests are welcome. For significant changes, open an issue first to discuss the direction.

License
MIT — see LICENSE.
