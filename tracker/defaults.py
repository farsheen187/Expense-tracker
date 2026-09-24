DEFAULT_CATEGORIES = [
    # Expenses
    {"name": "Food", "type": "expense", "color": "#EF4444"},
    {"name": "Transport", "type": "expense", "color": "#F59E0B"},
    {"name": "Shopping", "type": "expense", "color": "#EC4899"},
    {"name": "Bills", "type": "expense", "color": "#8B5CF6"},
    {"name": "Entertainment", "type": "expense", "color": "#06B6D4"},
    {"name": "Health", "type": "expense", "color": "#10B981"},
    {"name": "Other", "type": "expense", "color": "#6B7280"},
    # Income
    {"name": "Salary", "type": "income", "color": "#22C55E"},
    {"name": "Freelance", "type": "income", "color": "#3B82F6"},
    {"name": "Other", "type": "income", "color": "#6B7280"},
]


def seed_default_categories(user):
    """Create default income/expense categories for a new user."""
    from tracker.models import Category

    Category.objects.bulk_create(
        [
            Category(
                user=user,
                name=item["name"],
                type=item["type"],
                color=item["color"],
            )
            for item in DEFAULT_CATEGORIES
        ]
    )
