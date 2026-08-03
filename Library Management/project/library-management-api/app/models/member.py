"""Member model — represents a library member."""

from app.models.base_model import BaseModel
from app.database import query


class Member(BaseModel):
    """Domain model for the `members` table."""

    _table_name = "members"
    _fields = [
        "name",
        "email",
        "phone",
        "address",
        "membership_date",
        "membership_status",
        "max_books_allowed",
    ]

    @classmethod
    def find_by_email(cls, email):
        """Look up a member by email. Returns instance or None."""
        sql = "SELECT * FROM members WHERE email = %s"
        row = query(sql, (email,), fetch_one=True)
        return cls(row) if row else None

    @classmethod
    def search(cls, keyword=None, status=None, limit=100, offset=0):
        """
        Search members by keyword (name/email/phone) or membership status.
        Uses ILIKE for case-insensitive matching.
        """
        conditions = []
        params = []

        if keyword:
            conditions.append(
                "(name ILIKE %s OR email ILIKE %s OR phone ILIKE %s)"
            )
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        if status:
            conditions.append("membership_status = %s")
            params.append(status)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        params.extend([limit, offset])

        sql = (
            f"SELECT * FROM {cls._table_name} "
            f"WHERE {where_clause} "
            f"ORDER BY name ASC LIMIT %s OFFSET %s"
        )
        rows = query(sql, tuple(params))
        return cls._from_rows(rows)

    @classmethod
    def count_active_loans(cls, member_id):
        """
        Count the number of books currently borrowed by a member
        (status is 'issued' or 'overdue'). Used to enforce borrowing limits.
        """
        sql = """
            SELECT COUNT(*) AS active_loans
            FROM issue_records
            WHERE member_id = %s AND status IN ('issued', 'overdue')
        """
        row = query(sql, (member_id,), fetch_one=True)
        return row["active_loans"] if row else 0

    @classmethod
    def get_borrow_history(cls, member_id):
        """
        Get full borrow history for a member with book details.
        Uses a JOIN to the books table.
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
                b.isbn AS book_isbn
            FROM issue_records ir
            INNER JOIN books b ON ir.book_id = b.id
            WHERE ir.member_id = %s
            ORDER BY ir.issue_date DESC
        """
        return query(sql, (member_id,))

    @classmethod
    def get_active_loans(cls, member_id):
        """
        Get books currently borrowed by a member (not yet returned).
        """
        sql = """
            SELECT
                ir.id,
                ir.issue_date,
                ir.due_date,
                ir.status,
                ir.fine_amount,
                b.title AS book_title,
                b.author AS book_author,
                b.isbn AS book_isbn
            FROM issue_records ir
            INNER JOIN books b ON ir.book_id = b.id
            WHERE ir.member_id = %s AND ir.status IN ('issued', 'overdue')
            ORDER BY ir.due_date ASC
        """
        return query(sql, (member_id,))

    @classmethod
    def get_total_fines(cls, member_id):
        """Calculate total outstanding fines for a member."""
        sql = """
            SELECT COALESCE(SUM(fine_amount), 0) AS total_fines
            FROM issue_records
            WHERE member_id = %s
        """
        row = query(sql, (member_id,), fetch_one=True)
        return float(row["total_fines"]) if row else 0.0
