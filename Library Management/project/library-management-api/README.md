# Library Management REST API

A production-ready RESTful backend for managing books, members, and issue/return records. Built with Flask and PostgreSQL, applying OOP principles for clean, maintainable module structure.

## Features

- **Book Management** — Full CRUD for books with search, filtering by category/author, and borrow history tracking
- **Member Management** — Full CRUD for members with search, active loans view, and fine tracking
- **Issue / Return System** — Book lending with automatic due-date calculation, availability tracking, borrowing limits, and duplicate-loan prevention
- **Overdue Tracking** — Automatic overdue status updates, overdue listing with days overdue, and fine calculation
- **Borrow History** — Complete transaction history with SQL JOINs across books, members, and issue records
- **Dashboard** — Aggregate library statistics (total books, active members, issued/overdue counts, fines collected)
- **Consistent API** — Standardized JSON response format across all endpoints
- **Pagination** — Built-in pagination for all list endpoints
- **Input Validation** — Required field validation, type checking, and constraint error handling

## Technology Stack

| Layer            | Technology                     |
|------------------|--------------------------------|
| Framework        | Flask 3.1                      |
| Database         | PostgreSQL (Supabase-compatible) |
| DB Driver        | psycopg2 with connection pool  |
| Architecture     | OOP (Model–Service–Controller) |
| WSGI Server      | Gunicorn (production)          |
| Testing          | Postman collection included    |

## Project Structure

```
library-management-api/
├── app/
│   ├── __init__.py              # Package init
│   ├── app_factory.py           # Application factory (create_app)
│   ├── database.py              # Connection pool & query helper
│   ├── models/                  # OOP data models (inherit from BaseModel)
│   │   ├── __init__.py
│   │   ├── base_model.py        # BaseModel: generic CRUD via inheritance
│   │   ├── book.py              # Book model + search/borrow-history queries
│   │   ├── member.py            # Member model + search/loan/fine queries
│   │   └── issue_record.py      # IssueRecord model + overdue/fine logic
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── book_service.py      # Book business rules
│   │   ├── member_service.py    # Member business rules
│   │   └── issue_service.py     # Issue/return/fine/dashboard logic
│   ├── controllers/             # REST endpoints (Flask Blueprints)
│   │   ├── __init__.py
│   │   ├── book_controller.py   # /api/books
│   │   ├── member_controller.py # /api/members
│   │   └── issue_controller.py  # /api/issues
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       ├── responses.py         # Standardized JSON response helpers
│       └── validators.py        # Input validation & pagination helpers
├── postman/
│   └── library_management_api.postman_collection.json
├── config.py                    # Environment-based configuration
├── run.py                       # WSGI entry point
├── seed.py                      # Sample data seeder
├── setup.sh                     # Automated setup script
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── README.md                    # This file
```

## Architecture (OOP)

The project follows a layered OOP architecture:

1. **Models** (`app/models/`) — Each entity (Book, Member, IssueRecord) inherits from `BaseModel`, which provides generic `find_by_id`, `find_all`, `create`, `update`, `delete_by_id`, and `count` methods. Subclasses add domain-specific queries (search, JOINs, aggregate counts).

2. **Services** (`app/services/`) — Business logic lives here. Services enforce rules like borrowing limits, duplicate-loan prevention, overdue fine calculation, and referential-integrity error handling. Controllers never touch the database directly.

3. **Controllers** (`app/controllers/`) — Flask Blueprints that handle HTTP request parsing, input validation, and response formatting. They delegate all business logic to services.

4. **Database** (`app/database.py`) — A threaded connection pool (`psycopg2.pool.ThreadedConnectionPool`) manages PostgreSQL connections. The `query()` helper executes SQL with parameterized placeholders, auto-commits on success, and auto-rolls-back on error.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher (local install or cloud — Supabase, Neon, etc.)

## Installation & Setup

### Option A: Automated Setup (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh
```

### Option B: Manual Setup

1. **Clone or download the project folder**

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Linux/Mac
   # venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your `DATABASE_URL`:
   ```
   # Local PostgreSQL:
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/library_db

   # Supabase (find this in Project Settings > Database > Connection string):
   DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
   ```

5. **Create the database schema**
   The SQL schema is included in `schema.sql`. Run it against your database:
   ```bash
   psql "your-database-url" -f schema.sql
   ```
   Or execute the SQL from `schema.sql` in your database admin tool (pgAdmin, DBeaver, Supabase SQL Editor, etc.).

6. **(Optional) Seed sample data**
   ```bash
   python seed.py
   ```

7. **Start the server**
   ```bash
   python run.py
   ```
   The API will be available at `http://localhost:5000`

### Production Deployment

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## API Endpoints

All endpoints return JSON with a consistent structure:
```json
{
  "success": true,
  "message": "Description",
  "data": { ... },
  "meta": { ... }
}
```

### Books

| Method | Endpoint                        | Description                          |
|--------|---------------------------------|--------------------------------------|
| GET    | `/api/books`                    | List all books (paginated)           |
| GET    | `/api/books/search`             | Search by keyword, category, author  |
| GET    | `/api/books/<id>`               | Get a single book                    |
| GET    | `/api/books/<id>/history`       | Get borrow history for a book        |
| POST   | `/api/books`                    | Create a new book                    |
| PUT    | `/api/books/<id>`               | Update a book                        |
| DELETE | `/api/books/<id>`               | Delete a book                        |

### Members

| Method | Endpoint                         | Description                          |
|--------|----------------------------------|--------------------------------------|
| GET    | `/api/members`                   | List all members (paginated)         |
| GET    | `/api/members/search`            | Search by keyword or status          |
| GET    | `/api/members/<id>`              | Get a single member                  |
| GET    | `/api/members/<id>/history`      | Get borrow history for a member      |
| GET    | `/api/members/<id>/loans`        | Get active loans for a member        |
| GET    | `/api/members/<id>/fines`        | Get fine summary for a member        |
| POST   | `/api/members`                   | Create a new member                  |
| PUT    | `/api/members/<id>`              | Update a member                      |
| DELETE | `/api/members/<id>`              | Delete a member                      |

### Issue / Return

| Method | Endpoint                         | Description                          |
|--------|----------------------------------|--------------------------------------|
| GET    | `/api/issues`                    | List all issue records (paginated)   |
| GET    | `/api/issues/overdue`            | List all overdue records             |
| GET    | `/api/issues/<id>`               | Get a single issue record            |
| POST   | `/api/issues/issue`              | Issue a book to a member             |
| POST   | `/api/issues/<id>/return`        | Process a book return                |
| GET    | `/api/issues/dashboard`          | Get library statistics summary       |

### Query Parameters

- **Pagination**: `?page=1&per_page=20` (max 100 per page)
- **Book search**: `?keyword=gatsby&category=Fiction&author=fitzgerald`
- **Member search**: `?keyword=alice&status=active`

## Testing with Postman

1. Open Postman
2. Click **Import** > **File**
3. Select `postman/library_management_api.postman_collection.json`
4. Set the `base_url` environment variable to `http://localhost:5000`
5. Run the requests in order — the collection auto-captures created IDs into variables

## Database Schema

### books
| Column             | Type      | Constraints                     |
|--------------------|-----------|---------------------------------|
| id                 | UUID      | PK, auto-generated              |
| title              | text      | NOT NULL                        |
| author             | text      | NOT NULL                        |
| isbn               | text      | UNIQUE                          |
| category           | text      | default 'General'               |
| total_copies       | integer   | NOT NULL, >= 0                  |
| available_copies   | integer   | NOT NULL, >= 0, <= total_copies |
| publication_year   | integer   |                                 |
| publisher          | text      |                                 |
| shelf_location     | text      |                                 |
| created_at         | timestamp | default now()                   |
| updated_at         | timestamp | default now()                   |

### members
| Column              | Type      | Constraints                        |
|---------------------|-----------|------------------------------------|
| id                  | UUID      | PK, auto-generated                 |
| name                | text      | NOT NULL                           |
| email               | text      | UNIQUE, NOT NULL                   |
| phone               | text      |                                    |
| address             | text      |                                    |
| membership_date     | date      | default today                      |
| membership_status   | text      | 'active' or 'inactive'             |
| max_books_allowed   | integer   | default 5, > 0                     |
| created_at          | timestamp | default now()                      |
| updated_at          | timestamp | default now()                      |

### issue_records
| Column        | Type      | Constraints                                  |
|---------------|-----------|----------------------------------------------|
| id            | UUID      | PK, auto-generated                           |
| book_id       | UUID      | FK -> books(id), NOT NULL                    |
| member_id     | UUID      | FK -> members(id), NOT NULL                  |
| issue_date    | date      | NOT NULL, default today                      |
| due_date      | date      | NOT NULL, must be after issue_date           |
| return_date   | date      | nullable, must be >= issue_date              |
| status        | text      | 'issued', 'returned', or 'overdue'           |
| fine_amount   | numeric   | default 0.00, >= 0                           |
| created_at    | timestamp | default now()                                |
| updated_at    | timestamp | default now()                                |

## Business Rules Enforced

1. **Availability check** — A book cannot be issued if `available_copies` is 0
2. **Borrowing limit** — A member cannot exceed their `max_books_allowed` (default 5)
3. **Duplicate loan prevention** — A member cannot borrow the same book twice simultaneously
4. **Active members only** — Inactive members cannot borrow books
5. **Due date validation** — Due date must be after the issue date
6. **Overdue auto-detection** — Records past their due date are automatically marked 'overdue'
7. **Fine calculation** — Late returns incur a fine of $2.00/day past the due date (configurable)
8. **Referential integrity** — Books and members with active loans cannot be deleted

## Configuration

Environment variables (set in `.env`):

| Variable                   | Default                          | Description                        |
|----------------------------|----------------------------------|------------------------------------|
| `DATABASE_URL`             | postgresql://postgres:postgres@localhost:5432/library_db | PostgreSQL connection string |
| `FLASK_ENV`                | development                      | development / production / testing |
| `SECRET_KEY`               | dev-secret-key-change-in-production | Flask secret key               |
| `DEFAULT_LOAN_PERIOD_DAYS` | 14                               | Days before a book is due          |
| `FINE_PER_DAY`             | 2.00                             | Fine amount per overdue day        |

## License

This project is provided as-is for educational and portfolio use.
