"""Onboarding mode worker for background email processing"""
import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.database import async_session_maker
from app.config import settings
from app.services.gmail_service import GmailService
from app.services.labeling_service import LabelingService


class OnboardingWorker:
    """Background worker for onboarding mode email processing"""

    def __init__(self):
        """Initialize the onboarding worker"""
        self.gmail_token = settings.GMAIL_TOKEN
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.running = False

    async def process_user_emails(self, user: User, db: AsyncSession) -> None:
        """
        Process emails for a single user

        Args:
            user: User model instance
            db: Database session
        """
        try:
            # Initialize services
            gmail_service = GmailService(self.gmail_token)
            labeling_service = LabelingService(self.anthropic_api_key, gmail_service)

            # Call emailReader to get the next 5 emails
            email_reader_output = await gmail_service.email_reader(user.last_pointer)

            # Check if we got any emails
            if not email_reader_output.get('emails'):
                print(f"No emails to process for user {user.email}")
                return

            # For each email, call labelEmail
            await labeling_service.label_email(email_reader_output)

            # Save the new last_pointer and last_sync in the user table
            user.last_pointer = email_reader_output.get('nextPointer')
            user.last_sync = datetime.utcnow()

            # If no more emails (no nextPointer), mark onboarding as complete
            if not email_reader_output.get('nextPointer'):
                user.onboarding_complete = 1
                print(f"Onboarding complete for user {user.email}")
            else:
                print(f"Processed 5 emails for user {user.email}, more emails remaining")

            await db.commit()

        except Exception as e:
            print(f"Error processing emails for user {user.email}: {e}")
            await db.rollback()

    async def run_onboarding_cycle(self) -> None:
        """
        Run one cycle of the onboarding process

        Processes emails for all users who have not completed onboarding
        """
        async with async_session_maker() as db:
            try:
                # Get all users who have not completed onboarding
                # and have existing emails (last_pointer is not None or is None for first run)
                query = select(User).where(User.onboarding_complete == 0)
                result = await db.execute(query)
                users = result.scalars().all()

                if not users:
                    print("No users in onboarding mode")
                    return

                print(f"Processing emails for {len(users)} user(s)")

                # Process each user's emails
                for user in users:
                    print(f"Processing user: {user.email}")
                    await self.process_user_emails(user, db)

            except Exception as e:
                print(f"Error in onboarding cycle: {e}")

    async def start(self) -> None:
        """
        Start the onboarding worker

        Runs every 30 seconds, processing emails for users in onboarding mode
        """
        if not self.gmail_token or not self.anthropic_api_key:
            print("ERROR: Gmail token or Anthropic API key not configured")
            print("Please set GMAIL_TOKEN and ANTHROPIC_API_KEY in .env")
            return

        self.running = True
        print("Onboarding worker started")
        print("Running every 30 seconds...")

        try:
            while self.running:
                print(f"\n[{datetime.utcnow().isoformat()}] Running onboarding cycle...")

                await self.run_onboarding_cycle()

                print("Waiting 30 seconds until next cycle...")
                await asyncio.sleep(30)

        except KeyboardInterrupt:
            print("\nOnboarding worker stopped by user")
        except Exception as e:
            print(f"Onboarding worker error: {e}")
        finally:
            self.running = False

    def stop(self) -> None:
        """Stop the onboarding worker"""
        self.running = False
        print("Stopping onboarding worker...")
