"""Book controller — REST endpoints for book management."""

from flask import Blueprint, request
from app.services.book_service import BookService
from app.utils.responses import success_response, error_response, paginated_response
from app.utils.validators import (
    validate_required_fields,
    get_pagination_params,
    validate_positive_int,
)

books_bp = Blueprint("books", __name__, url_prefix="/api/books")


@books_bp.route("", methods=["GET"])
def get_books():
    """GET /api/books — List all books with pagination."""
    page, per_page, limit, offset = get_pagination_params(request.args)
    books, total = BookService.get_all_books(page, per_page, limit, offset)
    return paginated_response(books, total, page, per_page, "Books retrieved")


@books_bp.route("/search", methods=["GET"])
def search_books():
    """GET /api/books/search — Search books by keyword, category, or author."""
    results = BookService.search_books(request.args)
    return success_response(results, "Search results", 200, meta={"count": len(results)})


@books_bp.route("/<uuid:book_id>", methods=["GET"])
def get_book(book_id):
    """GET /api/books/<id> — Get a single book."""
    book = BookService.get_book(book_id)
    if not book:
        return error_response("Book not found", 404)
    return success_response(book, "Book retrieved")


@books_bp.route("/<uuid:book_id>/history", methods=["GET"])
def get_book_history(book_id):
    """GET /api/books/<id>/history — Get borrow history for a book."""
    history, error = BookService.get_book_history(book_id)
    if error:
        return error_response(error, 404)
    return success_response(history, "Borrow history retrieved",
                            meta={"count": len(history)})


@books_bp.route("", methods=["POST"])
def create_book():
    """POST /api/books — Create a new book."""
    data = request.get_json(silent=True)
    valid, err = validate_required_fields(data, ["title", "author"])
    if not valid:
        return err

    if "total_copies" in data:
        ok, err = validate_positive_int(data["total_copies"], "total_copies")
        if not ok:
            return err
        data.setdefault("available_copies", data["total_copies"])

    try:
        book = BookService.create_book(data)
        if not book:
            return error_response("Failed to create book", 500)
        return success_response(book, "Book created", 201)
    except Exception as e:
        msg = str(e)
        if "isbn" in msg.lower() and "unique" in msg.lower():
            return error_response("A book with this ISBN already exists", 409)
        return error_response("Failed to create book", 500)


@books_bp.route("/<uuid:book_id>", methods=["PUT"])
def update_book(book_id):
    """PUT /api/books/<id> — Update a book."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body is empty", 400)

    if "total_copies" in data:
        ok, err = validate_positive_int(data["total_copies"], "total_copies")
        if not ok:
            return err

    try:
        book = BookService.update_book(book_id, data)
        if not book:
            return error_response("Book not found", 404)
        return success_response(book, "Book updated")
    except Exception as e:
        msg = str(e)
        if "isbn" in msg.lower() and "unique" in msg.lower():
            return error_response("A book with this ISBN already exists", 409)
        if "available_not_exceed_total" in msg.lower() or "check" in msg.lower():
            return error_response(
                "Available copies cannot exceed total copies", 400
            )
        return error_response("Failed to update book", 500)


@books_bp.route("/<uuid:book_id>", methods=["DELETE"])
def delete_book(book_id):
    """DELETE /api/books/<id> — Delete a book."""
    deleted, error = BookService.delete_book(book_id)
    if error:
        status = 404 if "not found" in error.lower() else 409
        return error_response(error, status)
    return success_response(None, "Book deleted")
