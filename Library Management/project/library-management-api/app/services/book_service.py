"""Book service — business logic for book management operations."""

from app.models.book import Book
from app.models.issue_record import IssueRecord


class BookService:
    """Service layer for book-related business operations."""

    @staticmethod
    def get_all_books(page, per_page, limit, offset):
        """Retrieve paginated list of all books."""
        books = Book.find_all(limit=limit, offset=offset)
        total = Book.count()
        return [b.to_dict() for b in books], total

    @staticmethod
    def get_book(book_id):
        """Retrieve a single book by ID."""
        book = Book.find_by_id(book_id)
        if not book:
            return None
        return book.to_dict()

    @staticmethod
    def search_books(args):
        """Search books by keyword, category, or author."""
        keyword = args.get("keyword")
        category = args.get("category")
        author = args.get("author")
        books = Book.search(keyword=keyword, category=category, author=author)
        return [b.to_dict() for b in books]

    @staticmethod
    def create_book(data):
        """Create a new book record."""
        book = Book.create(data)
        if not book:
            return None
        return book.to_dict()

    @staticmethod
    def update_book(book_id, data):
        """Update an existing book."""
        book = Book.find_by_id(book_id)
        if not book:
            return None
        book.update(data)
        return book.to_dict()

    @staticmethod
    def delete_book(book_id):
        """Delete a book. Fails if the book has active loans (FK constraint)."""
        book = Book.find_by_id(book_id)
        if not book:
            return False, "Book not found"
        try:
            Book.delete_by_id(book_id)
            return True, None
        except Exception as e:
            if "foreign key" in str(e).lower() or "on delete restrict" in str(e).lower():
                return False, "Cannot delete book with active loan records"
            raise

    @staticmethod
    def get_book_history(book_id):
        """Get the complete borrow history for a specific book."""
        book = Book.find_by_id(book_id)
        if not book:
            return None, "Book not found"
        history = Book.get_borrow_history(book_id)
        return [dict(row) for row in history], None
