"""
Seed script — populates the database with sample data for testing.

Run:
    python seed.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app_factory import create_app
from app.models.book import Book
from app.models.member import Member
from app.models.issue_record import IssueRecord
from app.database import query
from datetime import date, timedelta


def seed_data():
    app = create_app()
    with app.app_context():
        existing = query("SELECT COUNT(*) AS c FROM books", fetch_one=True)
        if existing and existing["c"] > 0:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding books...")
        books_data = [
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald",
             "isbn": "978-0743273565", "category": "Fiction", "total_copies": 5,
             "publication_year": 1925, "publisher": "Scribner", "shelf_location": "A-12"},
            {"title": "To Kill a Mockingbird", "author": "Harper Lee",
             "isbn": "978-0061120084", "category": "Fiction", "total_copies": 3,
             "publication_year": 1960, "publisher": "HarperCollins", "shelf_location": "A-15"},
            {"title": "A Brief History of Time", "author": "Stephen Hawking",
             "isbn": "978-0553380163", "category": "Science", "total_copies": 4,
             "publication_year": 1988, "publisher": "Bantam", "shelf_location": "B-03"},
            {"title": "The Selfish Gene", "author": "Richard Dawkins",
             "isbn": "978-0198788607", "category": "Science", "total_copies": 2,
             "publication_year": 1976, "publisher": "Oxford University Press", "shelf_location": "B-05"},
            {"title": "Clean Code", "author": "Robert C. Martin",
             "isbn": "978-0132350884", "category": "Technology", "total_copies": 6,
             "publication_year": 2008, "publisher": "Prentice Hall", "shelf_location": "C-01"},
            {"title": "Design Patterns", "author": "Erich Gamma",
             "isbn": "978-0201633610", "category": "Technology", "total_copies": 3,
             "publication_year": 1994, "publisher": "Addison-Wesley", "shelf_location": "C-04"},
            {"title": "1984", "author": "George Orwell",
             "isbn": "978-0451524935", "category": "Fiction", "total_copies": 4,
             "publication_year": 1949, "publisher": "Signet Classic", "shelf_location": "A-20"},
            {"title": "Sapiens", "author": "Yuval Noah Harari",
             "isbn": "978-0062316097", "category": "History", "total_copies": 5,
             "publication_year": 2011, "publisher": "Harper", "shelf_location": "D-10"},
            {"title": "The Pragmatic Programmer", "author": "Andrew Hunt",
             "isbn": "978-0201616224", "category": "Technology", "total_copies": 4,
             "publication_year": 1999, "publisher": "Addison-Wesley", "shelf_location": "C-08"},
            {"title": "Atomic Habits", "author": "James Clear",
             "isbn": "978-0735211292", "category": "Self-Help", "total_copies": 8,
             "publication_year": 2018, "publisher": "Avery", "shelf_location": "E-02"},
        ]

        created_books = []
        for bd in books_data:
            bd["available_copies"] = bd["total_copies"]
            book = Book.create(bd)
            created_books.append(book)
            print(f"  Created book: {book.title}")

        print("\nSeeding members...")
        members_data = [
            {"name": "Alice Johnson", "email": "alice.johnson@example.com",
             "phone": "555-0101", "address": "123 Maple Street, Springfield"},
            {"name": "Bob Smith", "email": "bob.smith@example.com",
             "phone": "555-0102", "address": "456 Oak Avenue, Riverton"},
            {"name": "Carol Williams", "email": "carol.williams@example.com",
             "phone": "555-0103", "address": "789 Pine Road, Lakeside"},
            {"name": "David Brown", "email": "david.brown@example.com",
             "phone": "555-0104", "address": "321 Elm Street, Hilltown"},
            {"name": "Eva Davis", "email": "eva.davis@example.com",
             "phone": "555-0105", "address": "654 Cedar Lane, Valleyview"},
        ]

        created_members = []
        for md in members_data:
            member = Member.create(md)
            created_members.append(member)
            print(f"  Created member: {member.name}")

        print("\nSeeding issue records...")
        today = date.today()

        # Active loan (issued, not overdue)
        record1 = IssueRecord.create({
            "book_id": created_books[0].id,
            "member_id": created_members[0].id,
            "issue_date": today - timedelta(days=3),
            "due_date": today + timedelta(days=11),
            "status": "issued",
        })
        Book.decrement_available(created_books[0].id)
        print(f"  Issued '{created_books[0].title}' to {created_members[0].name}")

        # Active loan (issued, not overdue)
        record2 = IssueRecord.create({
            "book_id": created_books[4].id,
            "member_id": created_members[1].id,
            "issue_date": today - timedelta(days=5),
            "due_date": today + timedelta(days=9),
            "status": "issued",
        })
        Book.decrement_available(created_books[4].id)
        print(f"  Issued '{created_books[4].title}' to {created_members[1].name}")

        # Overdue loan
        record3 = IssueRecord.create({
            "book_id": created_books[6].id,
            "member_id": created_members[2].id,
            "issue_date": today - timedelta(days=25),
            "due_date": today - timedelta(days=11),
            "status": "issued",
        })
        Book.decrement_available(created_books[6].id)
        print(f"  Issued '{created_books[6].title}' to {created_members[2].name} (will be overdue)")

        # Returned loan
        record4 = IssueRecord.create({
            "book_id": created_books[7].id,
            "member_id": created_members[3].id,
            "issue_date": today - timedelta(days=20),
            "due_date": today - timedelta(days=6),
            "return_date": today - timedelta(days=8),
            "status": "returned",
            "fine_amount": 0.00,
        })
        print(f"  Returned '{created_books[7].title}' from {created_members[3].name}")

        # Returned loan with fine
        record5 = IssueRecord.create({
            "book_id": created_books[2].id,
            "member_id": created_members[4].id,
            "issue_date": today - timedelta(days=30),
            "due_date": today - timedelta(days=16),
            "return_date": today - timedelta(days=10),
            "status": "returned",
            "fine_amount": 12.00,
        })
        print(f"  Returned '{created_books[2].title}' from {created_members[4].name} (with fine)")

        print(f"\nSeeding complete! Created {len(books_data)} books, "
              f"{len(members_data)} members, 5 issue records.")


if __name__ == "__main__":
    seed_data()
