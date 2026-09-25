"""Shared owner for public (unauthenticated) API access."""

from django.contrib.auth import get_user_model

PUBLIC_USERNAME = "public_api"


def get_public_user():
    """
    Return the shared public user used when auth is not required.
    Creates the user and default categories on first use.
    """
    from tracker.defaults import seed_default_categories

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=PUBLIC_USERNAME,
        defaults={"email": "public@expense-tracker.local"},
    )
    if created:
        user.set_unusable_password()
        user.save()
        seed_default_categories(user)
    elif not user.categories.exists():
        seed_default_categories(user)
    return user
