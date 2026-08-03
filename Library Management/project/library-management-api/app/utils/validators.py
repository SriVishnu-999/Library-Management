"""Input validation utilities for API requests."""

from app.utils.responses import error_response


def validate_required_fields(data, required_fields):
    """
    Check that all required fields are present and non-empty in the request data.
    Returns (True, None) on success, (False, error_response) on failure.
    """
    if not data:
        return False, error_response("Request body is empty", 400)

    missing = []
    for field in required_fields:
        if field not in data or data[field] is None or (
            isinstance(data[field], str) and data[field].strip() == ""
        ):
            missing.append(field)

    if missing:
        return False, error_response(
            f"Missing required fields: {', '.join(missing)}",
            400,
            errors={"missing_fields": missing},
        )
    return True, None


def validate_positive_int(value, field_name):
    """Validate that a value is a positive integer. Returns (True, None) or (False, error)."""
    try:
        val = int(value)
        if val < 0:
            return False, error_response(
                f"{field_name} must be a non-negative integer", 400
            )
        return True, None
    except (TypeError, ValueError):
        return False, error_response(f"{field_name} must be a valid integer", 400)


def get_pagination_params(args):
    """Extract and validate page/per_page from query string. Defaults: page=1, per_page=20."""
    try:
        page = max(1, int(args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = min(100, max(1, int(args.get("per_page", 20))))
    except (TypeError, ValueError):
        per_page = 20

    limit = per_page
    offset = (page - 1) * per_page
    return page, per_page, limit, offset
