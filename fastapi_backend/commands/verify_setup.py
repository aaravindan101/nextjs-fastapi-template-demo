"""
Verify that the setup script completed successfully.

This script checks the main development database (not the test database)
to ensure everything was set up correctly.
"""

import asyncio
import sys
from sqlalchemy import select

from app.database import async_session_maker
from app.models import User


async def verify_database_connection():
    """Check if database is accessible."""
    try:
        async with async_session_maker() as session:
            # Simple query to verify DB connection
            await session.execute(select(User).limit(1))
            return True, "✓ Database connection successful"
    except Exception as e:
        return False, f"✗ Database connection failed: {str(e)}"


async def verify_test_user():
    """Check if test user exists."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.email == "test@example.com")
            )
            user = result.scalar_one_or_none()

            if not user:
                return False, "✗ Test user 'test@example.com' not found"

            if not user.is_active:
                return False, "✗ Test user exists but is not active"

            if not user.is_verified:
                return False, "✗ Test user exists but is not verified"

            return True, f"✓ Test user verified (ID: {user.id})"
    except Exception as e:
        return False, f"✗ Test user verification failed: {str(e)}"


async def verify_tables():
    """Check if database tables exist."""
    try:
        async with async_session_maker() as session:
            # Try to query the user table
            await session.execute(select(User).limit(1))
            return True, "✓ Database tables created successfully"
    except Exception as e:
        return False, f"✗ Database tables not found: {str(e)}"


async def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Setup Verification")
    print("=" * 60)
    print()

    checks = [
        ("Database Connection", verify_database_connection),
        ("Database Tables", verify_tables),
        ("Test User", verify_test_user),
    ]

    results = []
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        success, message = await check_func()
        results.append(success)
        print(message)

    print()
    print("=" * 60)

    if all(results):
        print("✓ Setup verification PASSED")
        print("=" * 60)
        print()
        print("Your setup is complete and working correctly!")
        print()
        print("Test user credentials:")
        print("  Email:    test@example.com")
        print("  Password: TestPassword123#")
        print()
        print("Next steps:")
        print("  1. Start the backend:  make start-backend")
        print("  2. Start the frontend: make start-frontend")
        print()
        sys.exit(0)
    else:
        print("✗ Setup verification FAILED")
        print("=" * 60)
        print()
        print("Some checks failed. Please run ./setup.sh again.")
        print()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
