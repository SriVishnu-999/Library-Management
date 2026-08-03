"""Issue/Return controller — REST endpoints for lending operations."""

from flask import Blueprint, request
from app.services.issue_service import IssueService
from app.utils.responses import success_response, error_response, paginated_response
from app.utils.validators import (
    validate_required_fields,
    get_pagination_params,
)

issue_bp = Blueprint("issues", __name__, url_prefix="/api/issues")


@issue_bp.route("", methods=["GET"])
def get_all_records():
    """GET /api/issues — Get all borrow records with details (paginated)."""
    page, per_page, limit, offset = get_pagination_params(request.args)
    records = IssueService.get_all_records(page, per_page, limit, offset)
    return success_response(
        records, "Borrow records retrieved",
        meta={"page": page, "per_page": per_page, "count": len(records)},
    )


@issue_bp.route("/overdue", methods=["GET"])
def get_overdue():
    """GET /api/issues/overdue — Get all overdue records with details."""
    page, per_page, limit, offset = get_pagination_params(request.args)
    records, total = IssueService.get_overdue_records(page, per_page, limit, offset)
    return paginated_response(
        records, total, page, per_page, "Overdue records retrieved"
    )


@issue_bp.route("/<uuid:record_id>", methods=["GET"])
def get_record(record_id):
    """GET /api/issues/<id> — Get a single issue record with details."""
    record = IssueService.get_record(record_id)
    if not record:
        return error_response("Issue record not found", 404)
    return success_response(record, "Issue record retrieved")


@issue_bp.route("/issue", methods=["POST"])
def issue_book():
    """POST /api/issues/issue — Issue a book to a member."""
    data = request.get_json(silent=True)
    valid, err = validate_required_fields(data, ["book_id", "member_id"])
    if not valid:
        return err

    try:
        result, error = IssueService.issue_book(data)
        if error:
            return error_response(error, 400)
        return success_response(result, "Book issued successfully", 201)
    except Exception as e:
        return error_response(f"Failed to issue book: {str(e)}", 500)


@issue_bp.route("/<uuid:record_id>/return", methods=["POST"])
def return_book(record_id):
    """POST /api/issues/<id>/return — Process a book return."""
    data = request.get_json(silent=True)
    try:
        result, error = IssueService.return_book(record_id, data)
        if error:
            status = 404 if "not found" in error.lower() else 400
            return error_response(error, status)
        message = "Book returned successfully"
        if result.get("was_overdue"):
            message += f" (overdue fine: ${result.get('fine_amount', 0):.2f})"
        return success_response(result, message)
    except Exception as e:
        return error_response(f"Failed to return book: {str(e)}", 500)


@issue_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """GET /api/issues/dashboard — Get library statistics summary."""
    stats = IssueService.get_dashboard_stats()
    return success_response(stats, "Dashboard statistics retrieved")
