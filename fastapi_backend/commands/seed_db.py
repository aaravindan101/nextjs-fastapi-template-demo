"""
Database seeding script for creating test users.

This script creates a default test user for development and testing purposes.
It's idempotent - safe to run multiple times (won't create duplicates).

Usage:
    PYTHONPATH=. uv run python3 commands/seed_db.py
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi_users.password import PasswordHelper

from app.database import async_session_maker
from app.models import User


async def seed_test_user():
    """Create a test user if it doesn't already exist."""

    test_user_email = "test@example.com"
    test_user_password = "TestPassword123#"

    async with async_session_maker() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == test_user_email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✓ Test user already exists: {test_user_email}")
            print(f"  ID: {existing_user.id}")
            print(f"  Active: {existing_user.is_active}")
            print(f"  Verified: {existing_user.is_verified}")
            return existing_user

        # Create new test user
        password_helper = PasswordHelper()
        hashed_password = password_helper.hash(test_user_password)

        user = User(
            id=uuid.uuid4(),
            email=test_user_email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            is_verified=True,  # Pre-verified for easier testing
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        print(f"✓ Created test user: {test_user_email}")
        print(f"  ID: {user.id}")
        print(f"  Password: {test_user_password}")
        print(f"  Active: {user.is_active}")
        print(f"  Verified: {user.is_verified}")

        return user


async def main():
    """Main function to seed the database."""
    print("=" * 60)
    print("Database Seeding")
    print("=" * 60)
    print()

    await seed_test_user()

    print()
    print("=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print()
    print("You can now log in with:")
    print("  Email:    test@example.com")
    print("  Password: TestPassword123#")
    print()


if __name__ == "__main__":
    asyncio.run(main())
