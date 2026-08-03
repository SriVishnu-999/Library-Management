"""
End-to-end test for the Library Management REST API.
Tests the Flask application using the test client with a mocked database layer.

Run:
    python test_api.py
"""

import sys
import os
import uuid
from datetime import date
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app_factory import create_app
from config import TestingConfig


def make_test_app():
    """Create a Flask app with the database layer fully mocked."""
    with patch("app.app_factory.init_pool"), \
         patch("app.app_factory.close_pool"), \
         patch("app.app_factory.close_db"):
        app = create_app(TestingConfig)
    app.testing = True
    return app


# --- Mock query handler ---

MOCK_BOOKS = []
MOCK_MEMBERS = []
MOCK_ISSUES = []


def mock_query(sql, params=None, fetch_one=False, fetch_all=True):
    """Simulate database queries for testing."""
    from psycopg2.extras import RealDictRow

    sql_lower = sql.lower().strip()

    # Dashboard aggregate (must be first — contains many subqueries with count/from)
    if "total_books" in sql_lower and "total_copies" in sql_lower and "total_fines_collected" in sql_lower:
        return RealDictRow({
            "total_books": len(MOCK_BOOKS),
            "total_copies": sum(b["total_copies"] for b in MOCK_BOOKS),
            "available_copies": sum(b["available_copies"] for b in MOCK_BOOKS),
            "active_members": len(MOCK_MEMBERS),
            "total_members": len(MOCK_MEMBERS),
            "books_issued": len(MOCK_ISSUES),
            "books_overdue": 0,
            "books_returned": 0,
            "total_fines_collected": 0,
        })

    # COUNT queries
    if "count(*) as total" in sql_lower and "from books" in sql_lower:
        return RealDictRow({"total": len(MOCK_BOOKS)})
    if "count(*) as total" in sql_lower and "from members" in sql_lower:
        return RealDictRow({"total": len(MOCK_MEMBERS)})
    if "count(*) as active_loans" in sql_lower:
        return RealDictRow({"active_loans": 0})
    if "count(*) as total" in sql_lower and "from issue_records" in sql_lower:
        return RealDictRow({"total": len(MOCK_ISSUES)})
    if "coalesce(sum" in sql_lower and "fine_amount" in sql_lower:
        return RealDictRow({"total_fines": 0})

    # UPDATE overdue status (no-op in mock)
    if sql_lower.startswith("update issue_records") and "overdue" in sql_lower:
        return None

    # SELECT by ID
    if "where id = %s" in sql_lower and "from books" in sql_lower:
        for b in MOCK_BOOKS:
            if str(b["id"]) == str(params[0]):
                return RealDictRow(b) if fetch_one else [RealDictRow(b)]
        return None if fetch_one else []

    if "where id = %s" in sql_lower and "from members" in sql_lower:
        for m in MOCK_MEMBERS:
            if str(m["id"]) == str(params[0]):
                return RealDictRow(m) if fetch_one else [RealDictRow(m)]
        return None if fetch_one else []

    if "where id = %s" in sql_lower and "from issue_records" in sql_lower:
        for i in MOCK_ISSUES:
            if str(i["id"]) == str(params[0]):
                return RealDictRow(i) if fetch_one else [RealDictRow(i)]
        return None if fetch_one else []

    # SELECT all books
    if sql_lower.startswith("select * from books") and "order by created_at" in sql_lower:
        return [RealDictRow(b) for b in MOCK_BOOKS]

    # SELECT all members
    if sql_lower.startswith("select * from members") and "order by created_at" in sql_lower:
        return [RealDictRow(m) for m in MOCK_MEMBERS]

    # Search books
    if "from books" in sql_lower and "ilike" in sql_lower:
        return [RealDictRow(b) for b in MOCK_BOOKS]

    # Search members
    if "from members" in sql_lower and "ilike" in sql_lower:
        return [RealDictRow(m) for m in MOCK_MEMBERS]

    # JOIN queries (borrow history, overdue, dashboard detail)
    if "from issue_records ir" in sql_lower and "join" in sql_lower:
        results = []
        for i in MOCK_ISSUES:
            row = dict(i)
            row["book_title"] = "Test Book"
            row["book_author"] = "Test Author"
            row["member_name"] = "Test Member"
            row["member_email"] = "test@test.com"
            row["days_overdue"] = 0
            results.append(RealDictRow(row))
        return results

    # INSERT book
    if sql_lower.startswith("insert into books") and "returning" in sql_lower:
        new_book = {
            "id": uuid.uuid4(),
            "title": params[0] if params else "Test",
            "author": params[1] if len(params) > 1 else "Author",
            "isbn": None,
            "category": "General",
            "total_copies": 1,
            "available_copies": 1,
            "publication_year": None,
            "publisher": None,
            "shelf_location": None,
            "created_at": None,
            "updated_at": None,
        }
        MOCK_BOOKS.append(new_book)
        return RealDictRow(new_book) if fetch_one else [RealDictRow(new_book)]

    # UPDATE book available
    if "available_copies = available_copies" in sql_lower:
        return None

    # DELETE
    if sql_lower.startswith("delete from books"):
        return None
    if sql_lower.startswith("delete from members"):
        return None

    # Email lookup
    if "where email = %s" in sql_lower:
        return None if fetch_one else []

    # Default
    return None if fetch_one else []


def run_tests():
    """Run all tests and report results."""
    passed = 0
    failed = 0
    tests = []

    def test(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            tests.append(f"  PASS  {name}")
        else:
            failed += 1
            tests.append(f"  FAIL  {name}  {detail}")

    MOCK_BOOKS.clear()
    MOCK_MEMBERS.clear()
    MOCK_ISSUES.clear()

    app = make_test_app()
    app.testing = True
    client = app.test_client()

    query_patch_locations = [
        "app.database.query",
        "app.models.base_model.query",
        "app.models.book.query",
        "app.models.member.query",
        "app.models.issue_record.query",
        "app.services.issue_service.query",
    ]
    patches = [patch(loc, side_effect=mock_query) for loc in query_patch_locations]
    for p in patches:
        p.start()

    try:
        # --- App creation ---
        test("App creates successfully", app is not None)

        # --- 404 handler ---
        r = client.get("/api/nonexistent")
        d = r.get_json()
        test("404 returns JSON error", r.status_code == 404 and d["success"] is False)

        # --- 405 handler ---
        r = client.delete("/api/books/search")
        d = r.get_json()
        test("405 returns JSON error", r.status_code == 405 and d["success"] is False)

        # --- Books: GET list ---
        r = client.get("/api/books")
        d = r.get_json()
        test("GET /api/books returns 200", r.status_code == 200)
        test("GET /api/books has success=true", d["success"] is True)
        test("GET /api/books has pagination meta", "meta" in d and "page" in d["meta"])

        # --- Books: GET with pagination ---
        r = client.get("/api/books?page=2&per_page=5")
        d = r.get_json()
        test("Pagination page param works", d["meta"]["page"] == 2)
        test("Pagination per_page param works", d["meta"]["per_page"] == 5)

        # --- Books: max per_page cap ---
        r = client.get("/api/books?per_page=500")
        d = r.get_json()
        test("per_page capped at 100", d["meta"]["per_page"] == 100)

        # --- Books: search ---
        r = client.get("/api/books/search?keyword=test")
        d = r.get_json()
        test("GET /api/books/search returns 200", r.status_code == 200)
        test("Search has success=true", d["success"] is True)

        # --- Books: GET by ID not found ---
        r = client.get("/api/books/00000000-0000-0000-0000-000000000000")
        d = r.get_json()
        test("GET unknown book returns 404", r.status_code == 404)

        # --- Books: POST missing fields ---
        r = client.post("/api/books", json={"author": "Test"})
        d = r.get_json()
        test("POST book missing title returns 400", r.status_code == 400)
        test("Missing fields error has success=false", d["success"] is False)

        # --- Books: POST valid ---
        r = client.post("/api/books", json={
            "title": "Test Book",
            "author": "Test Author",
            "isbn": "111-222",
            "total_copies": 3,
        })
        d = r.get_json()
        test("POST valid book returns 201", r.status_code == 201)
        test("Created book has success=true", d["success"] is True)

        # --- Books: PUT not found ---
        r = client.put("/api/books/00000000-0000-0000-0000-000000000000",
                       json={"title": "Updated"})
        test("PUT unknown book returns 404", r.status_code == 404)

        # --- Books: DELETE not found ---
        r = client.delete("/api/books/00000000-0000-0000-0000-000000000000")
        test("DELETE unknown book returns 404", r.status_code == 404)

        # --- Books: history ---
        r = client.get("/api/books/00000000-0000-0000-0000-000000000000/history")
        test("GET book history unknown returns 404", r.status_code == 404)

        # --- Members: GET list ---
        r = client.get("/api/members")
        d = r.get_json()
        test("GET /api/members returns 200", r.status_code == 200)
        test("Members list has success=true", d["success"] is True)

        # --- Members: search ---
        r = client.get("/api/members/search?keyword=test")
        d = r.get_json()
        test("GET /api/members/search returns 200", r.status_code == 200)

        # --- Members: POST missing fields ---
        r = client.post("/api/members", json={"name": "Test"})
        test("POST member missing email returns 400", r.status_code == 400)

        # --- Members: GET by ID not found ---
        r = client.get("/api/members/00000000-0000-0000-0000-000000000000")
        test("GET unknown member returns 404", r.status_code == 404)

        # --- Members: history ---
        r = client.get("/api/members/00000000-0000-0000-0000-000000000000/history")
        test("GET member history unknown returns 404", r.status_code == 404)

        # --- Members: loans ---
        r = client.get("/api/members/00000000-0000-0000-0000-000000000000/loans")
        test("GET member loans unknown returns 404", r.status_code == 404)

        # --- Members: fines ---
        r = client.get("/api/members/00000000-0000-0000-0000-000000000000/fines")
        test("GET member fines unknown returns 404", r.status_code == 404)

        # --- Issues: GET list ---
        r = client.get("/api/issues")
        d = r.get_json()
        test("GET /api/issues returns 200", r.status_code == 200)
        test("Issues list has success=true", d["success"] is True)

        # --- Issues: overdue ---
        r = client.get("/api/issues/overdue")
        d = r.get_json()
        test("GET /api/issues/overdue returns 200", r.status_code == 200)
        test("Overdue list has success=true", d["success"] is True)

        # --- Issues: dashboard ---
        r = client.get("/api/issues/dashboard")
        d = r.get_json()
        test("GET /api/issues/dashboard returns 200", r.status_code == 200)
        test("Dashboard has success=true", d["success"] is True)
        test("Dashboard has total_books", "total_books" in d["data"])

        # --- Issues: GET by ID not found ---
        r = client.get("/api/issues/00000000-0000-0000-0000-000000000000")
        test("GET unknown issue returns 404", r.status_code == 404)

        # --- Issues: POST issue missing fields ---
        r = client.post("/api/issues/issue", json={"book_id": "test"})
        test("POST issue missing member_id returns 400", r.status_code == 400)

        # --- Issues: return not found ---
        r = client.post("/api/issues/00000000-0000-0000-0000-000000000000/return", json={})
        test("POST return unknown issue returns 404", r.status_code == 404)

    finally:
        for p in patches:
            p.stop()

    print()
    print("=" * 60)
    print("  Library Management REST API — Test Results")
    print("=" * 60)
    for t in tests:
        print(t)
    print("-" * 60)
    print(f"  Total: {passed + failed}  |  Passed: {passed}  |  Failed: {failed}")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
