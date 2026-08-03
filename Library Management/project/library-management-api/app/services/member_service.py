"""Member service — business logic for member management operations."""

from app.models.member import Member


class MemberService:
    """Service layer for member-related business operations."""

    @staticmethod
    def get_all_members(page, per_page, limit, offset):
        """Retrieve paginated list of all members."""
        members = Member.find_all(limit=limit, offset=offset)
        total = Member.count()
        return [m.to_dict() for m in members], total

    @staticmethod
    def get_member(member_id):
        """Retrieve a single member by ID."""
        member = Member.find_by_id(member_id)
        if not member:
            return None
        return member.to_dict()

    @staticmethod
    def search_members(args):
        """Search members by keyword or status."""
        keyword = args.get("keyword")
        status = args.get("status")
        members = Member.search(keyword=keyword, status=status)
        return [m.to_dict() for m in members]

    @staticmethod
    def create_member(data):
        """Create a new member. Checks for duplicate email."""
        existing = Member.find_by_email(data.get("email", ""))
        if existing:
            return None, "A member with this email already exists"
        member = Member.create(data)
        if not member:
            return None, "Failed to create member"
        return member.to_dict(), None

    @staticmethod
    def update_member(member_id, data):
        """Update an existing member."""
        member = Member.find_by_id(member_id)
        if not member:
            return None, "Member not found"
        if "email" in data and data["email"] != member.email:
            existing = Member.find_by_email(data["email"])
            if existing:
                return None, "A member with this email already exists"
        member.update(data)
        return member.to_dict(), None

    @staticmethod
    def delete_member(member_id):
        """Delete a member. Fails if member has active loans."""
        member = Member.find_by_id(member_id)
        if not member:
            return False, "Member not found"
        active = Member.count_active_loans(member_id)
        if active > 0:
            return False, f"Cannot delete member with {active} active loan(s). Return all books first."
        try:
            Member.delete_by_id(member_id)
            return True, None
        except Exception as e:
            if "foreign key" in str(e).lower():
                return False, "Cannot delete member with borrow history records"
            raise

    @staticmethod
    def get_member_history(member_id):
        """Get complete borrow history for a member."""
        member = Member.find_by_id(member_id)
        if not member:
            return None, "Member not found"
        history = Member.get_borrow_history(member_id)
        return [dict(row) for row in history], None

    @staticmethod
    def get_member_active_loans(member_id):
        """Get books currently borrowed by a member."""
        member = Member.find_by_id(member_id)
        if not member:
            return None, "Member not found"
        loans = Member.get_active_loans(member_id)
        return [dict(row) for row in loans], None

    @staticmethod
    def get_member_fines(member_id):
        """Get total outstanding fines for a member."""
        member = Member.find_by_id(member_id)
        if not member:
            return None, "Member not found"
        total = Member.get_total_fines(member_id)
        active = Member.count_active_loans(member_id)
        return {
            "member_id": str(member.id),
            "member_name": member.name,
            "total_fines": total,
            "active_loans": active,
        }, None
