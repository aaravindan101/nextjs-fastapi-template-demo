"""Email labeling service using Anthropic Claude API"""
from typing import Dict, Any, List
from anthropic import Anthropic
from .gmail_service import GmailService


class LabelingService:
    """Service for analyzing and labeling emails using AI"""

    # System Gmail labels to remove
    GMAIL_SYSTEM_LABELS = [
        "INBOX",
        "IMPORTANT",
        "STARRED",
        "CATEGORY_PROMOTIONS",
        "CATEGORY_UPDATES",
        "CATEGORY_SOCIAL",
        "CATEGORY_FORUMS"
    ]

    def __init__(self, anthropic_api_key: str, gmail_service: GmailService):
        """
        Initialize labeling service

        Args:
            anthropic_api_key: Anthropic API key
            gmail_service: Initialized GmailService instance
        """
        self.anthropic_client = Anthropic(api_key=anthropic_api_key)
        self.gmail_service = gmail_service

    def _analyze_with_anthropic(self, combined_text: str) -> str:
        """
        Analyze email content with Anthropic Claude

        Args:
            combined_text: Combined email body text

        Returns:
            Label category: 'action_needed', 'FYI', 'spam', or 'extra'
        """
        prompt = """Based on this email and its thread:
- If it asks the user to perform an action → respond with 'action_needed'
- If it provides useful information → respond with 'FYI'
- If it contains suspicious files or short URLs → respond with 'spam'
- Otherwise → respond with 'extra'

Return only one word: action_needed, FYI, spam, or extra.

Email content:
"""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": prompt + combined_text
                    }
                ]
            )

            # Extract the response text
            label = message.content[0].text.strip().lower()

            # Validate response
            valid_labels = ['action_needed', 'fyi', 'spam', 'extra']
            if label not in valid_labels:
                # Default to 'extra' if unexpected response
                return 'extra'

            return label

        except Exception as e:
            print(f"Error analyzing with Anthropic: {e}")
            # Default to 'extra' on error
            return 'extra'

    async def label_email(self, email_reader_output: Dict[str, Any]) -> str:
        """
        Label emails from emailReader output

        Args:
            email_reader_output: Output from GmailService.email_reader()

        Returns:
            Success message
        """
        emails = email_reader_output.get('emails', [])

        for email in emails:
            main_email = email.get('mainEmail')
            thread_messages = email.get('threadMessages', [])

            if not main_email:
                continue

            # Skip labeling if this email is a thread message
            if main_email.get('isThreadMessage'):
                continue

            # Combine message bodies (main + thread) for context analysis
            combined_text = main_email.get('body', '')

            for msg in thread_messages:
                body = msg.get('body', '')
                if body:
                    combined_text += "\n" + body

            # Step 1: Analyze content with Anthropic model
            label = self._analyze_with_anthropic(combined_text)

            # Step 2: Clear existing Gmail labels from this message
            try:
                self.gmail_service.modify_message_labels(
                    message_id=main_email['id'],
                    remove_label_ids=self.GMAIL_SYSTEM_LABELS
                )
            except Exception as e:
                print(f"Error removing labels from message {main_email['id']}: {e}")
                # Continue even if label removal fails

            # Step 3: Determine Gmail label name
            label_name_map = {
                'action_needed': 'ACTION_NEEDED',
                'fyi': 'FYI',
                'spam': 'SPAM',
                'extra': 'EXTRA'
            }

            label_name = label_name_map.get(label, 'EXTRA')

            # Step 4: Get or create Gmail label ID
            try:
                label_id = self.gmail_service.get_or_create_label_id(label_name)

                # Step 5: Apply new label
                self.gmail_service.modify_message_labels(
                    message_id=main_email['id'],
                    add_label_ids=[label_id]
                )

                print(f"Labeled email {main_email['id']} as {label_name}")

            except Exception as e:
                print(f"Error applying label to message {main_email['id']}: {e}")
                # Continue processing other emails

        return "Labeling complete"
