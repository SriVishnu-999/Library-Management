"""Database connection management using a connection pool."""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from flask import g, current_app

_pool = None


def init_pool():
    """Initialize the global connection pool. Call once at app startup."""
    global _pool
    if _pool is not None:
        return
    _pool = pool.ThreadedConnectionPool(
        minconn=2,
        maxconn=10,
        dsn=current_app.config["DATABASE_URL"],
    )


def close_pool():
    """Close all connections in the pool. Call on app shutdown."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


def get_db():
    """Get a database connection for the current request."""
    if "db" not in g:
        if _pool is None:
            init_pool()
        g.db = _pool.getconn()
    return g.db


def get_cursor():
    """Get a RealDictCursor on the current request's connection."""
    return get_db().cursor(cursor_factory=RealDictCursor)


def commit():
    """Commit the current request's transaction."""
    if "db" in g:
        g.db.commit()


def rollback():
    """Roll back the current request's transaction."""
    if "db" in g:
        g.db.rollback()


def close_db(error=None):
    """Return the connection to the pool at end of request."""
    db = g.pop("db", None)
    if db is not None and _pool is not None:
        if error is not None:
            _pool.putconn(db, close=True)
        else:
            _pool.putconn(db)


def query(sql, params=None, fetch_one=False, fetch_all=True):
    """
    Execute a SQL query and return results.

    Args:
        sql: SQL query string with %s placeholders.
        params: Tuple or dict of parameters for the query.
        fetch_one: If True, return a single row dict (or None).
        fetch_all: If True and not fetch_one, return list of row dicts.

    Returns:
        For SELECT: list of dicts or a single dict.
        For INSERT/UPDATE/DELETE: the affected row dict(s) if RETURNING used.
    """
    cursor = get_cursor()
    try:
        cursor.execute(sql, params)
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
        commit()
        return result
    except Exception:
        rollback()
        raise
    finally:
        cursor.close()
