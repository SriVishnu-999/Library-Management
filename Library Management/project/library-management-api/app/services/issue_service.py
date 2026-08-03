"""Issue/Return service — core business logic for book lending operations."""

from datetime import date
from app.models.book import Book
from app.models.member import Member
from app.models.issue_record import IssueRecord
from app.database import query
import psycopg2


class IssueService:
    """Service layer for issue/return (borrow) operations."""

    @staticmethod
    def get_all_records(page, per_page, limit, offset):
        """Retrieve paginated borrow history with book and member details."""
        IssueRecord.update_overdue_status()
        records = IssueRecord.get_borrow_history_with_details(limit=limit, offset=offset)
        return [IssueService._serialize_record(r) for r in records]

    @staticmethod
    def get_record(record_id):
        """Get a single issue record with details."""
        IssueRecord.update_overdue_status()
        row = IssueRecord.get_by_id_with_details(record_id)
        if not row:
            return None
        return IssueService._serialize_record(row)

    @staticmethod
    def issue_book(data):
        """
        Issue a book to a member. Business rules:
        1. Book must exist and have available copies.
        2. Member must exist and be active.
        3. Member must not exceed borrowing limit.
        4. Member must not already have an active loan for this book.
        """
        book_id = data.get("book_id")
        member_id = data.get("member_id")
        loan_days = data.get("loan_period_days")

        book = Book.find_by_id(book_id)
        if not book:
            return None, "Book not found"

        if book.available_copies <= 0:
            return None, f"No available copies of '{book.title}'"

        member = Member.find_by_id(member_id)
        if not member:
            return None, "Member not found"

        if member.membership_status != "active":
            return None, f"Member '{member.name}' is not active"

        active_loans = Member.count_active_loans(member_id)
        if active_loans >= member.max_books_allowed:
            return None, (
                f"Member has reached the borrowing limit "
                f"({active_loans}/{member.max_books_allowed} books)"
            )

        existing = IssueRecord.find_active_by_book_and_member(book_id, member_id)
        if existing:
            return None, "Member already has an active loan for this book"

        issue_date = date.today()
        due_date = IssueRecord.get_due_date(
            issue_date=issue_date, loan_period_days=loan_days
        )

        record = IssueRecord.create({
            "book_id": book_id,
            "member_id": member_id,
            "issue_date": issue_date,
            "due_date": due_date,
            "status": "issued",
        })

        if not record:
            return None, "Failed to create issue record"

        Book.decrement_available(book_id)

        return IssueService._format_issue_response(record, book, member), None

    @staticmethod
    def return_book(record_id, data=None):
        """
        Process a book return. Business rules:
        1. Record must exist and not already be returned.
        2. Calculate fine if return is overdue.
        3. Mark record as returned and increment book availability.
        """
        record = IssueRecord.find_by_id(record_id)
        if not record:
            return None, "Issue record not found"

        if record.status == "returned":
            return None, "This book has already been returned"

        return_date = date.today()
        if data and data.get("return_date"):
            return_date = date.fromisoformat(data["return_date"])

        fine = IssueRecord.calculate_fine(record, return_date)
        new_status = "returned"
        if return_date > record.due_date:
            new_status = "returned"

        updated = record.update({
            "return_date": return_date,
            "status": new_status,
            "fine_amount": fine,
        })

        Book.increment_available(record.book_id)

        book = Book.find_by_id(record.book_id)
        member = Member.find_by_id(record.member_id)

        result = updated.to_dict()
        result["book_title"] = book.title if book else None
        result["book_author"] = book.author if book else None
        result["member_name"] = member.name if member else None
        result["was_overdue"] = fine > 0
        return result, None

    @staticmethod
    def get_overdue_records(page, per_page, limit, offset):
        """Get all overdue records with details and days overdue."""
        IssueRecord.update_overdue_status()
        rows = IssueRecord.find_all_overdue(limit=limit, offset=offset)
        total = IssueRecord.get_overdue_count()
        records = [IssueService._serialize_record(r) for r in rows]
        return records, total

    @staticmethod
    def get_dashboard_stats():
        """Aggregate statistics for the library dashboard."""
        IssueRecord.update_overdue_status()

        sql = """
            SELECT
                (SELECT COUNT(*) FROM books) AS total_books,
                (SELECT COALESCE(SUM(total_copies), 0) FROM books) AS total_copies,
                (SELECT COALESCE(SUM(available_copies), 0) FROM books) AS available_copies,
                (SELECT COUNT(*) FROM members WHERE membership_status = 'active') AS active_members,
                (SELECT COUNT(*) FROM members) AS total_members,
                (SELECT COUNT(*) FROM issue_records WHERE status = 'issued') AS books_issued,
                (SELECT COUNT(*) FROM issue_records WHERE status = 'overdue') AS books_overdue,
                (SELECT COUNT(*) FROM issue_records WHERE status = 'returned') AS books_returned,
                (SELECT COALESCE(SUM(fine_amount), 0) FROM issue_records) AS total_fines_collected
        """
        row = query(sql, fetch_one=True)
        if row:
            return {
                "total_books": row["total_books"],
                "total_copies": row["total_copies"],
                "available_copies": row["available_copies"],
                "borrowed_copies": row["total_copies"] - row["available_copies"],
                "total_members": row["total_members"],
                "active_members": row["active_members"],
                "books_issued": row["books_issued"],
                "books_overdue": row["books_overdue"],
                "books_returned": row["books_returned"],
                "total_fines_collected": float(row["total_fines_collected"]),
            }
        return {}

    @staticmethod
    def _format_issue_response(record, book, member):
        """Format the issue response with book and member details."""
        result = record.to_dict()
        result["book_title"] = book.title
        result["book_author"] = book.author
        result["member_name"] = member.name
        result["member_email"] = member.email
        return result

    @staticmethod
    def _serialize_record(row):
        """Convert a RealDictRow with joined data into a serializable dict."""
        result = {}
        for key, value in dict(row).items():
            if isinstance(value, date):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
