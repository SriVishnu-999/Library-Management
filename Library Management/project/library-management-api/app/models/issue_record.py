"""IssueRecord model — tracks book issue and return transactions."""

from datetime import date, timedelta
from app.models.base_model import BaseModel
from app.database import query


class IssueRecord(BaseModel):
    """Domain model for the `issue_records` table."""

    _table_name = "issue_records"
    _fields = [
        "book_id",
        "member_id",
        "issue_date",
        "due_date",
        "return_date",
        "status",
        "fine_amount",
    ]

    @classmethod
    def find_active_by_book_and_member(cls, book_id, member_id):
        """
        Check if a member already has an active loan for a given book.
        Returns the existing record or None.
        """
        sql = """
            SELECT * FROM issue_records
            WHERE book_id = %s AND member_id = %s
              AND status IN ('issued', 'overdue')
        """
        row = query(sql, (book_id, member_id), fetch_one=True)
        return cls(row) if row else None

    @classmethod
    def find_all_overdue(cls, limit=100, offset=0):
        """
        Get all overdue records with member and book details.
        Joins both members and books tables.
        """
        sql = """
            SELECT
                ir.id,
                ir.issue_date,
                ir.due_date,
                ir.return_date,
                ir.status,
                ir.fine_amount,
                b.title AS book_title,
                b.author AS book_author,
                b.isbn AS book_isbn,
                m.name AS member_name,
                m.email AS member_email,
                m.phone AS member_phone,
                CURRENT_DATE - ir.due_date AS days_overdue
            FROM issue_records ir
            INNER JOIN books b ON ir.book_id = b.id
            INNER JOIN members m ON ir.member_id = m.id
            WHERE ir.status = 'overdue'
            ORDER BY ir.due_date ASC
            LIMIT %s OFFSET %s
        """
        rows = query(sql, (limit, offset))
        return rows or []

    @classmethod
    def update_overdue_status(cls):
        """
        Mark all records past their due_date and not yet returned as 'overdue'.
        Called automatically before any overdue query.
        """
        sql = """
            UPDATE issue_records
            SET status = 'overdue'
            WHERE status = 'issued'
              AND return_date IS NULL
              AND due_date < CURRENT_DATE
        """
        query(sql, fetch_all=False)

    @classmethod
    def get_overdue_count(cls):
        """Count of currently overdue records."""
        sql = """
            SELECT COUNT(*) AS total
            FROM issue_records
            WHERE status = 'overdue'
        """
        row = query(sql, fetch_one=True)
        return row["total"] if row else 0

    @classmethod
    def get_borrow_history_with_details(cls, limit=100, offset=0):
        """
        Get complete borrow history with book and member info.
        Full JOIN across all three tables.
        """
        sql = """
            SELECT
                ir.id,
                ir.issue_date,
                ir.due_date,
                ir.return_date,
                ir.status,
                ir.fine_amount,
                b.title AS book_title,
                b.author AS book_author,
                b.isbn AS book_isbn,
                b.category AS book_category,
                m.name AS member_name,
                m.email AS member_email
            FROM issue_records ir
            INNER JOIN books b ON ir.book_id = b.id
            INNER JOIN members m ON ir.member_id = m.id
            ORDER BY ir.issue_date DESC
            LIMIT %s OFFSET %s
        """
        rows = query(sql, (limit, offset))
        return rows or []

    @classmethod
    def get_by_id_with_details(cls, record_id):
        """Get a single issue record with joined book and member details."""
        sql = """
            SELECT
                ir.*,
                b.title AS book_title,
                b.author AS book_author,
                b.isbn AS book_isbn,
                m.name AS member_name,
                m.email AS member_email
            FROM issue_records ir
            INNER JOIN books b ON ir.book_id = b.id
            INNER JOIN members m ON ir.member_id = m.id
            WHERE ir.id = %s
        """
        row = query(sql, (record_id,), fetch_one=True)
        return row

    @classmethod
    def calculate_fine(cls, issue_record, return_date=None):
        """
        Calculate the fine for a late return.
        Fine = days_overdue * fine_per_day.
        """
        from flask import current_app

        fine_per_day = current_app.config.get("FINE_PER_DAY", 2.0)
        actual_return = return_date or date.today()

        if actual_return <= issue_record.due_date:
            return 0.0

        days_overdue = (actual_return - issue_record.due_date).days
        return float(days_overdue * fine_per_day)

    @classmethod
    def get_due_date(cls, issue_date=None, loan_period_days=None):
        """Calculate the due date from issue date and loan period."""
        from flask import current_app

        days = loan_period_days or current_app.config.get(
            "DEFAULT_LOAN_PERIOD_DAYS", 14
        )
        base_date = issue_date or date.today()
        return base_date + timedelta(days=days)
