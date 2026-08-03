# 📚 Library Management REST API

A RESTful backend application built with **Python, Flask, and PostgreSQL** for managing books, library members, and borrowing records. The project follows Object-Oriented Programming principles and provides clean REST APIs for CRUD operations.

---

## 🚀 Features

- 📖 Manage books
- 👥 Manage library members
- 🔄 Issue and return books
- 📅 Borrow history tracking
- ⚠️ Overdue book detection
- ✅ RESTful CRUD APIs
- 🗄 PostgreSQL relational database
- 🧪 Tested using Postman

---

## 🛠 Tech Stack

- Python
- Flask
- PostgreSQL
- SQLAlchemy
- Postman
- OOP

---

## 📂 Project Structure

```
library-management-api/
│
├── app.py
├── config.py
├── models/
├── routes/
├── services/
├── database/
├── requirements.txt
└── README.md
```

---

## Database

Tables:

- Books
- Members
- Borrow Records

Relationships:

```
Member
   │
   ├──── BorrowRecord ──── Book
```

---

## API Endpoints

### Books

| Method | Endpoint | Description |
|---------|----------|------------|
| GET | /books | Get all books |
| GET | /books/<id> | Get book |
| POST | /books | Add book |
| PUT | /books/<id> | Update book |
| DELETE | /books/<id> | Delete book |

### Members

| Method | Endpoint |
|---------|----------|
| GET | /members |
| POST | /members |
| PUT | /members/<id> |
| DELETE | /members/<id> |

### Borrow Records

| Method | Endpoint |
|---------|----------|
| POST | /borrow |
| POST | /return |
| GET | /history |

---

## Installation

```bash
git clone https://github.com/yourusername/library-management-api.git

cd library-management-api

pip install -r requirements.txt

createdb library_db

python app.py
```

---

## Example API

```http
POST /books
```

```json
{
  "title":"Atomic Habits",
  "author":"James Clear",
  "copies":5
}
```

---

## Future Improvements

- JWT Authentication
- Docker
- Swagger Documentation
- Unit Testing
- Pagination

---

## Author

Your Name
