"""Member controller — REST endpoints for member management."""

from flask import Blueprint, request
from app.services.member_service import MemberService
from app.utils.responses import success_response, error_response, paginated_response
from app.utils.validators import (
    validate_required_fields,
    get_pagination_params,
    validate_positive_int,
)

members_bp = Blueprint("members", __name__, url_prefix="/api/members")


@members_bp.route("", methods=["GET"])
def get_members():
    """GET /api/members — List all members with pagination."""
    page, per_page, limit, offset = get_pagination_params(request.args)
    members, total = MemberService.get_all_members(page, per_page, limit, offset)
    return paginated_response(members, total, page, per_page, "Members retrieved")


@members_bp.route("/search", methods=["GET"])
def search_members():
    """GET /api/members/search — Search members by keyword or status."""
    results = MemberService.search_members(request.args)
    return success_response(results, "Search results", 200, meta={"count": len(results)})


@members_bp.route("/<uuid:member_id>", methods=["GET"])
def get_member(member_id):
    """GET /api/members/<id> — Get a single member."""
    member = MemberService.get_member(member_id)
    if not member:
        return error_response("Member not found", 404)
    return success_response(member, "Member retrieved")


@members_bp.route("/<uuid:member_id>/history", methods=["GET"])
def get_member_history(member_id):
    """GET /api/members/<id>/history — Get borrow history for a member."""
    history, error = MemberService.get_member_history(member_id)
    if error:
        return error_response(error, 404)
    return success_response(history, "Borrow history retrieved",
                            meta={"count": len(history)})


@members_bp.route("/<uuid:member_id>/loans", methods=["GET"])
def get_member_loans(member_id):
    """GET /api/members/<id>/loans — Get active loans for a member."""
    loans, error = MemberService.get_member_active_loans(member_id)
    if error:
        return error_response(error, 404)
    return success_response(loans, "Active loans retrieved",
                            meta={"count": len(loans)})


@members_bp.route("/<uuid:member_id>/fines", methods=["GET"])
def get_member_fines(member_id):
    """GET /api/members/<id>/fines — Get fine summary for a member."""
    fines, error = MemberService.get_member_fines(member_id)
    if error:
        return error_response(error, 404)
    return success_response(fines, "Fine summary retrieved")


@members_bp.route("", methods=["POST"])
def create_member():
    """POST /api/members — Create a new member."""
    data = request.get_json(silent=True)
    valid, err = validate_required_fields(data, ["name", "email"])
    if not valid:
        return err

    if "max_books_allowed" in data:
        ok, err = validate_positive_int(data["max_books_allowed"], "max_books_allowed")
        if not ok:
            return err

    try:
        member, error = MemberService.create_member(data)
        if error:
            return error_response(error, 409)
        return success_response(member, "Member created", 201)
    except Exception as e:
        return error_response("Failed to create member", 500)


@members_bp.route("/<uuid:member_id>", methods=["PUT"])
def update_member(member_id):
    """PUT /api/members/<id> — Update a member."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body is empty", 400)

    try:
        member, error = MemberService.update_member(member_id, data)
        if error:
            status = 404 if "not found" in error.lower() else 409
            return error_response(error, status)
        return success_response(member, "Member updated")
    except Exception as e:
        return error_response("Failed to update member", 500)


@members_bp.route("/<uuid:member_id>", methods=["DELETE"])
def delete_member(member_id):
    """DELETE /api/members/<id> — Delete a member."""
    deleted, error = MemberService.delete_member(member_id)
    if error:
        status = 404 if "not found" in error.lower() else 409
        return error_response(error, status)
    return success_response(None, "Member deleted")
