"""Book model — represents a library book entry."""

from app.models.base_model import BaseModel
from app.database import query


class Book(BaseModel):
    """Domain model for the `books` table."""

    _table_name = "books"
    _fields = [
        "title",
        "author",
        "isbn",
        "category",
        "total_copies",
        "available_copies",
        "publication_year",
        "publisher",
        "shelf_location",
    ]

    @classmethod
    def search(cls, keyword=None, category=None, author=None, limit=100, offset=0):
        """
        Search books by keyword (title/author/isbn), category, or author.
        Uses ILIKE for case-insensitive matching.
        """
        conditions = []
        params = []

        if keyword:
            conditions.append(
                "(title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s)"
            )
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        if category:
            conditions.append("category = %s")
            params.append(category)

        if author:
            conditions.append("author ILIKE %s")
            params.append(f"%{author}%")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        params.extend([limit, offset])

        sql = (
            f"SELECT * FROM {cls._table_name} "
            f"WHERE {where_clause} "
            f"ORDER BY title ASC LIMIT %s OFFSET %s"
        )
        rows = query(sql, tuple(params))
        return cls._from_rows(rows)

    @classmethod
    def decrement_available(cls, book_id):
        """Reduce available_copies by 1 (when a book is issued)."""
        sql = (
            "UPDATE books SET available_copies = available_copies - 1 "
            "WHERE id = %s AND available_copies > 0 RETURNING *"
        )
        row = query(sql, (book_id,), fetch_one=True)
        return cls(row) if row else None

    @classmethod
    def increment_available(cls, book_id):
        """Increase available_copies by 1 (when a book is returned)."""
        sql = (
            "UPDATE books SET available_copies = available_copies + 1 "
            "WHERE id = %s AND available_copies < total_copies RETURNING *"
        )
        row = query(sql, (book_id,), fetch_one=True)
        return cls(row) if row else None

    @classmethod
    def get_available_count(cls, book_id):
        """Get current available_copies for a book."""
        sql = "SELECT available_copies FROM books WHERE id = %s"
        row = query(sql, (book_id,), fetch_one=True)
        return row["available_copies"] if row else None

    @classmethod
    def get_borrow_history(cls, book_id):
        """
        Get full borrow history for a book with member details.
        Uses a JOIN to the members table.
        """
        sql = """
            SELECT
                ir.id,
                ir.issue_date,
                ir.due_date,
                ir.return_date,
                ir.status,
                ir.fine_amount,
                m.name AS member_name,
                m.email AS member_email
            FROM issue_records ir
            INNER JOIN members m ON ir.member_id = m.id
            WHERE ir.book_id = %s
            ORDER BY ir.issue_date DESC
        """
        return query(sql, (book_id,))
