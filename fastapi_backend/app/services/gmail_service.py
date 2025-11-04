"""Gmail API service for reading emails and threads"""
import base64
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailService:
    """Service for interacting with Gmail API"""

    def __init__(self, gmail_token: str):
        """
        Initialize Gmail service with OAuth token

        Args:
            gmail_token: OAuth2 access token for Gmail API
        """
        self.credentials = Credentials(token=gmail_token)
        self.service = build('gmail', 'v1', credentials=self.credentials)

    def _extract_headers(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract relevant headers from email"""
        header_dict = {}
        header_names = ['Date', 'From', 'To', 'Subject']

        for header in headers:
            if header['name'] in header_names:
                header_dict[header['name']] = header['value']

        return header_dict

    def _decode_body(self, data: Optional[str]) -> str:
        """Decode base64 encoded email body"""
        if not data:
            return ""

        try:
            # Gmail uses URL-safe base64 encoding
            decoded_bytes = base64.urlsafe_b64decode(data)
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception:
            return ""

    def _find_body_in_parts(self, parts: Optional[List[Dict[str, Any]]]) -> str:
        """
        Find and extract email body from parts

        Tries to find plain text or HTML body in the message parts
        """
        if not parts:
            return ""

        body_text = ""

        for part in parts:
            mime_type = part.get('mimeType', '')

            # Check for nested parts (multipart)
            if 'parts' in part:
                body_text = self._find_body_in_parts(part['parts'])
                if body_text:
                    return body_text

            # Try plain text first
            if mime_type == 'text/plain' and 'data' in part.get('body', {}):
                return self._decode_body(part['body']['data'])

            # Fall back to HTML
            if mime_type == 'text/html' and 'data' in part.get('body', {}):
                body_text = self._decode_body(part['body']['data'])

        return body_text

    def _extract_attachments(self, parts: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract attachment information from message parts"""
        if not parts:
            return []

        attachments = []

        for part in parts:
            # Check for nested parts
            if 'parts' in part:
                attachments.extend(self._extract_attachments(part['parts']))

            # Check if this part is an attachment
            if part.get('filename') and 'body' in part:
                body = part['body']
                if body.get('attachmentId'):
                    attachments.append({
                        'filename': part['filename'],
                        'mimeType': part.get('mimeType', ''),
                        'size': body.get('size', 0),
                        'attachmentId': body['attachmentId']
                    })

        return attachments

    async def email_reader(self, last_pointer: Optional[str] = None) -> Dict[str, Any]:
        """
        Read latest 5 emails from Gmail with full thread context

        Args:
            last_pointer: Page token for pagination

        Returns:
            Dict containing nextPointer and list of emails with thread data
        """
        try:
            # Step 1: Get latest 5 emails from Gmail
            list_params = {
                'userId': 'me',
                'maxResults': 5
            }

            if last_pointer:
                list_params['pageToken'] = last_pointer

            response = self.service.users().messages().list(**list_params).execute()

            next_pointer = response.get('nextPageToken')
            messages = response.get('messages', [])

            result_emails = []

            # Step 2: For each message, get its full thread (conversation)
            for message in messages:
                thread = self.service.users().threads().get(
                    userId='me',
                    id=message['threadId'],
                    format='full'
                ).execute()

                thread_messages = []

                for msg in thread.get('messages', []):
                    payload = msg.get('payload', {})
                    headers = self._extract_headers(payload.get('headers', []))

                    # Try to read plain text or HTML body
                    body_text = ""
                    if 'parts' in payload:
                        body_text = self._find_body_in_parts(payload['parts'])
                    elif 'body' in payload and 'data' in payload['body']:
                        body_text = self._decode_body(payload['body']['data'])

                    # Collect attachments info (if any)
                    attachments = self._extract_attachments(payload.get('parts', []))

                    # Check if this is a thread message (more than 1 message in thread)
                    is_thread_message = len(thread.get('messages', [])) > 1

                    thread_messages.append({
                        'id': msg['id'],
                        'threadId': msg['threadId'],
                        'date': headers.get('Date', ''),
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'subject': headers.get('Subject', ''),
                        'snippet': msg.get('snippet', ''),
                        'body': body_text,
                        'attachments': attachments,
                        'isThreadMessage': is_thread_message
                    })

                # Main email is the first message in the thread
                main_email = thread_messages[0] if thread_messages else None

                if main_email:
                    result_emails.append({
                        'threadId': thread['id'],
                        'historyId': thread.get('historyId', ''),
                        'mainEmail': main_email,
                        'threadMessages': thread_messages
                    })

            return {
                'nextPointer': next_pointer,
                'emails': result_emails
            }

        except HttpError as error:
            raise Exception(f"Gmail API error: {error}")

    def get_or_create_label_id(self, label_name: str) -> str:
        """
        Get existing label ID or create new label

        Args:
            label_name: Name of the Gmail label

        Returns:
            Label ID string
        """
        try:
            # Get all labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    return label['id']

            # Create new label if it doesn't exist
            label_object = {
                'name': label_name,
                'messageListVisibility': 'show',
                'labelListVisibility': 'labelShow'
            }

            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()

            return created_label['id']

        except HttpError as error:
            raise Exception(f"Error managing Gmail labels: {error}")

    def modify_message_labels(
        self,
        message_id: str,
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None
    ) -> None:
        """
        Modify labels on a Gmail message

        Args:
            message_id: Gmail message ID
            add_label_ids: List of label IDs to add
            remove_label_ids: List of label IDs to remove
        """
        try:
            modify_body = {}

            if add_label_ids:
                modify_body['addLabelIds'] = add_label_ids

            if remove_label_ids:
                modify_body['removeLabelIds'] = remove_label_ids

            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=modify_body
            ).execute()

        except HttpError as error:
            raise Exception(f"Error modifying message labels: {error}")
