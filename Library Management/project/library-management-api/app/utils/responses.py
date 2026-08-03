"""Standardized API response helpers."""

from flask import jsonify


def success_response(data=None, message="Success", status_code=200, meta=None):
    """Build a standard success JSON response."""
    body = {
        "success": True,
        "message": message,
    }
    if data is not None:
        body["data"] = data
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status_code


def error_response(message="An error occurred", status_code=400, errors=None):
    """Build a standard error JSON response."""
    body = {
        "success": False,
        "message": message,
    }
    if errors is not None:
        body["errors"] = errors
    return jsonify(body), status_code


def paginated_response(data, total, page, per_page, message="Success"):
    """Build a paginated list response with metadata."""
    body = {
        "success": True,
        "message": message,
        "data": data,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
        },
    }
    return jsonify(body), 200
