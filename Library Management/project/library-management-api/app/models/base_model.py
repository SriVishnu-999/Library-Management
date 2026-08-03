"""Base model class providing common CRUD patterns via OOP inheritance."""

import uuid
from datetime import date
from app.database import query


class BaseModel:
    """
    Abstract base for all domain models. Subclasses define:
        _table_name: the PostgreSQL table name
        _primary_key: the primary key column name (default 'id')
        _fields: list of editable column names
    """

    _table_name = None
    _primary_key = "id"
    _fields = []

    def __init__(self, data):
        """Initialize from a RealDictRow or plain dict."""
        self._data = dict(data) if data else {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    @property
    def id(self):
        return self._data.get(self._primary_key)

    def to_dict(self):
        """Return a JSON-serializable dict with ISO-format dates."""
        result = {}
        for key, value in self._data.items():
            if isinstance(value, (date,)):
                result[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[key] = str(value)
            else:
                result[key] = value
        return result

    @classmethod
    def _from_rows(cls, rows):
        """Convert a list of RealDictRows into model instances."""
        return [cls(row) for row in rows] if rows else []

    @classmethod
    def find_by_id(cls, record_id):
        """Fetch a single record by primary key. Returns instance or None."""
        sql = f"SELECT * FROM {cls._table_name} WHERE {cls._primary_key} = %s"
        row = query(sql, (record_id,), fetch_one=True)
        return cls(row) if row else None

    @classmethod
    def find_all(cls, limit=100, offset=0):
        """Fetch paginated records."""
        sql = (
            f"SELECT * FROM {cls._table_name} "
            f"ORDER BY created_at DESC LIMIT %s OFFSET %s"
        )
        rows = query(sql, (limit, offset))
        return cls._from_rows(rows)

    @classmethod
    def count(cls):
        """Return total number of records."""
        sql = f"SELECT COUNT(*) AS total FROM {cls._table_name}"
        row = query(sql, fetch_one=True)
        return row["total"] if row else 0

    @classmethod
    def create(cls, data):
        """Insert a new record and return the created instance."""
        fields = [f for f in cls._fields if f in data]
        columns = ", ".join(fields)
        placeholders = ", ".join(["%s"] * len(fields))
        values = [data[f] for f in fields]
        sql = (
            f"INSERT INTO {cls._table_name} ({columns}) "
            f"VALUES ({placeholders}) "
            f"RETURNING *"
        )
        row = query(sql, tuple(values), fetch_one=True)
        return cls(row) if row else None

    def update(self, data):
        """Update fields on this instance and persist."""
        fields = [f for f in self._fields if f in data]
        if not fields:
            return self
        set_clause = ", ".join([f"{f} = %s" for f in fields])
        values = [data[f] for f in fields]
        values.append(self.id)
        sql = (
            f"UPDATE {self._table_name} SET {set_clause} "
            f"WHERE {self._primary_key} = %s RETURNING *"
        )
        row = query(sql, tuple(values), fetch_one=True)
        if row:
            self._data = dict(row)
        return self

    @classmethod
    def delete_by_id(cls, record_id):
        """Delete a record by primary key. Returns True if a row was deleted."""
        sql = f"DELETE FROM {cls._table_name} WHERE {cls._primary_key} = %s"
        result = query(sql, (record_id,), fetch_all=False)
        return True
