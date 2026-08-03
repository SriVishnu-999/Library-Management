-- ============================================================
-- Library Management Schema
-- ============================================================
-- Run this against your PostgreSQL database to create the schema.
-- Usage:
--   psql "postgresql://user:password@host:port/dbname" -f schema.sql
-- ============================================================

-- BOOKS TABLE
CREATE TABLE IF NOT EXISTS books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT UNIQUE,
    category TEXT DEFAULT 'General',
    total_copies INTEGER NOT NULL DEFAULT 1 CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
    publication_year INTEGER,
    publisher TEXT,
    shelf_location TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT books_available_not_exceed_total CHECK (available_copies <= total_copies)
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books (author);
CREATE INDEX IF NOT EXISTS idx_books_category ON books (category);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books (isbn);

-- MEMBERS TABLE
CREATE TABLE IF NOT EXISTS members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    membership_date DATE DEFAULT CURRENT_DATE,
    membership_status TEXT NOT NULL DEFAULT 'active' CHECK (membership_status IN ('active', 'inactive')),
    max_books_allowed INTEGER NOT NULL DEFAULT 5 CHECK (max_books_allowed > 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_members_email ON members (email);
CREATE INDEX IF NOT EXISTS idx_members_name ON members (name);
CREATE INDEX IF NOT EXISTS idx_members_status ON members (membership_status);

-- ISSUE RECORDS TABLE
CREATE TABLE IF NOT EXISTS issue_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    return_date DATE,
    status TEXT NOT NULL DEFAULT 'issued' CHECK (status IN ('issued', 'returned', 'overdue')),
    fine_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (fine_amount >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_due_after_issue CHECK (due_date > issue_date),
    CONSTRAINT chk_return_after_issue CHECK (return_date IS NULL OR return_date >= issue_date)
);

-- Prevent duplicate active loans for the same book+member
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_loan
    ON issue_records (book_id, member_id)
    WHERE status IN ('issued', 'overdue');

CREATE INDEX IF NOT EXISTS idx_issue_member ON issue_records (member_id);
CREATE INDEX IF NOT EXISTS idx_issue_book ON issue_records (book_id);
CREATE INDEX IF NOT EXISTS idx_issue_status ON issue_records (status);
CREATE INDEX IF NOT EXISTS idx_issue_due_date ON issue_records (due_date);

-- AUTO-UPDATE updated_at TRIGGER
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_books_updated_at ON books;
CREATE TRIGGER trg_books_updated_at
    BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_members_updated_at ON members;
CREATE TRIGGER trg_members_updated_at
    BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_issue_records_updated_at ON issue_records;
CREATE TRIGGER trg_issue_records_updated_at
    BEFORE UPDATE ON issue_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
