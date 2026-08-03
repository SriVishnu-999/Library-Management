/*
# Library Management Schema

## Overview
Creates the complete database schema for a Library Management REST API.
This is a single-tenant system (no user authentication) designed to manage
books, library members, and issue/return (borrow) records with overdue tracking.

## New Tables

### 1. books
- `id` (uuid, primary key) — unique book identifier
- `title` (text, not null) — book title
- `author` (text, not null) — book author
- `isbn` (text, unique) — ISBN number
- `category` (text) — genre/category (e.g. Fiction, Science)
- `total_copies` (int, not null, default 1) — total copies owned by library
- `available_copies` (int, not null, default = total_copies) — copies currently available for issue
- `publication_year` (int) — year of publication
- `publisher` (text) — publisher name
- `shelf_location` (text) — physical location in library
- `created_at` (timestamptz, default now())
- `updated_at` (timestamptz, default now())

### 2. members
- `id` (uuid, primary key) — unique member identifier
- `name` (text, not null) — member full name
- `email` (text, unique, not null) — email address
- `phone` (text) — phone number
- `address` (text) — home address
- `membership_date` (date, default today) — date member joined
- `membership_status` (text, default 'active') — 'active' or 'inactive'
- `max_books_allowed` (int, default 5) — borrowing limit
- `created_at` (timestamptz, default now())
- `updated_at` (timestamptz, default now())

### 3. issue_records
- `id` (uuid, primary key) — unique record identifier
- `book_id` (uuid, FK -> books.id) — which book was borrowed
- `member_id` (uuid, FK -> members.id) — which member borrowed
- `issue_date` (date, not null, default today) — date book was issued
- `due_date` (date, not null) — date book is due back
- `return_date` (date, nullable) — actual return date (null = not yet returned)
- `status` (text, default 'issued') — 'issued', 'returned', 'overdue'
- `fine_amount` (numeric, default 0) — fine for late return
- `created_at` (timestamptz, default now())
- `updated_at` (timestamptz, default now())

## Constraints
- `books.available_copies` >= 0 (CHECK constraint)
- `books.total_copies` >= 0 (CHECK constraint)
- `issue_records.due_date` > `issue_records.issue_date` (CHECK constraint)
- `issue_records.return_date` >= `issue_records.issue_date` when not null (CHECK constraint)
- `issue_records.fine_amount` >= 0 (CHECK constraint)
- Unique constraint preventing duplicate active loans for same book+member

## Indexes
- Index on books.title, books.author, books.category for search
- Index on members.email, members.name for lookup
- Index on issue_records.member_id, issue_records.book_id, issue_records.status for queries
- Index on issue_records.due_date for overdue tracking

## Security (RLS)
- This is a single-tenant system with no authentication.
- RLS enabled on all tables with full CRUD access for anon + authenticated roles.
- Data is intentionally shared/public for the library management use case.
*/

-- ============================================================
-- BOOKS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS books (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL,
    author text NOT NULL,
    isbn text UNIQUE,
    category text DEFAULT 'General',
    total_copies integer NOT NULL DEFAULT 1 CHECK (total_copies >= 0),
    available_copies integer NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
    publication_year integer,
    publisher text,
    shelf_location text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Ensure available_copies never exceeds total_copies
ALTER TABLE books DROP CONSTRAINT IF EXISTS books_available_not_exceed_total;
ALTER TABLE books ADD CONSTRAINT books_available_not_exceed_total
    CHECK (available_copies <= total_copies);

CREATE INDEX IF NOT EXISTS idx_books_title ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books (author);
CREATE INDEX IF NOT EXISTS idx_books_category ON books (category);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books (isbn);

ALTER TABLE books ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_books" ON books;
CREATE POLICY "anon_select_books" ON books FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_books" ON books;
CREATE POLICY "anon_insert_books" ON books FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_books" ON books;
CREATE POLICY "anon_update_books" ON books FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_books" ON books;
CREATE POLICY "anon_delete_books" ON books FOR DELETE
    TO anon, authenticated USING (true);

-- ============================================================
-- MEMBERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS members (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    email text UNIQUE NOT NULL,
    phone text,
    address text,
    membership_date date DEFAULT CURRENT_DATE,
    membership_status text NOT NULL DEFAULT 'active' CHECK (membership_status IN ('active', 'inactive')),
    max_books_allowed integer NOT NULL DEFAULT 5 CHECK (max_books_allowed > 0),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_members_email ON members (email);
CREATE INDEX IF NOT EXISTS idx_members_name ON members (name);
CREATE INDEX IF NOT EXISTS idx_members_status ON members (membership_status);

ALTER TABLE members ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_members" ON members;
CREATE POLICY "anon_select_members" ON members FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_members" ON members;
CREATE POLICY "anon_insert_members" ON members FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_members" ON members;
CREATE POLICY "anon_update_members" ON members FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_members" ON members;
CREATE POLICY "anon_delete_members" ON members FOR DELETE
    TO anon, authenticated USING (true);

-- ============================================================
-- ISSUE RECORDS TABLE (Borrow/Return tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS issue_records (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id uuid NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    member_id uuid NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    issue_date date NOT NULL DEFAULT CURRENT_DATE,
    due_date date NOT NULL,
    return_date date,
    status text NOT NULL DEFAULT 'issued' CHECK (status IN ('issued', 'returned', 'overdue')),
    fine_amount numeric(10, 2) NOT NULL DEFAULT 0.00 CHECK (fine_amount >= 0),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
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

ALTER TABLE issue_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_issue_records" ON issue_records;
CREATE POLICY "anon_select_issue_records" ON issue_records FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_issue_records" ON issue_records;
CREATE POLICY "anon_insert_issue_records" ON issue_records FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_issue_records" ON issue_records;
CREATE POLICY "anon_update_issue_records" ON issue_records FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_issue_records" ON issue_records;
CREATE POLICY "anon_delete_issue_records" ON issue_records FOR DELETE
    TO anon, authenticated USING (true);

-- ============================================================
-- AUTO-UPDATE updated_at TRIGGER
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
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