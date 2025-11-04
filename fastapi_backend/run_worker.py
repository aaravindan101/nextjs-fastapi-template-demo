#!/usr/bin/env python3
"""
Main script to run the onboarding worker

Usage:
    python run_worker.py
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.workers.onboarding_worker import OnboardingWorker


def main():
    """Main entry point for the worker"""
    print("=" * 60)
    print("Email Onboarding Worker")
    print("=" * 60)
    print()

    worker = OnboardingWorker()

    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        print("\nShutting down worker...")
        worker.stop()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
