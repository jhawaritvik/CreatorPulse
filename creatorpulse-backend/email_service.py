"""
Email service for sending newsletters to clients using SMTP.
Integrates with Supabase database to manage newsletters and recipients.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class EmailService:
    """Service for sending emails and managing newsletter campaigns."""
    
    def __init__(self):
        """Initialize the email service with SMTP configuration."""
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = os.environ.get("SMTP_USERNAME")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")
        self.from_email = os.environ.get("FROM_EMAIL", self.smtp_username)
        self.from_name = os.environ.get("FROM_NAME", "CreatorPulse")
        
        if not all([self.smtp_username, self.smtp_password]):
            raise ValueError("SMTP credentials must be set in .env file")
        
        self.supabase = get_supabase_client()
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: Optional[str] = None) -> bool:
        """
        Send an email to a single recipient.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    def create_newsletter(self, user_id: str, title: str, content: str, 
                         scheduled_time: Optional[datetime] = None) -> Optional[str]:
        """
        Create a new newsletter in the database.
        
        Args:
            user_id: ID of the user creating the newsletter
            title: Newsletter title
            content: Newsletter HTML content
            scheduled_time: When to send the newsletter (optional)
            
        Returns:
            str: Newsletter ID if created successfully, None otherwise
        """
        try:
            newsletter_data = {
                'user_id': user_id,
                'title': title,
                'content': content,
                'status': 'draft',
                'scheduled_time': scheduled_time.isoformat() if scheduled_time else None,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table('newsletters').insert(newsletter_data).execute()
            
            if response.data:
                newsletter_id = response.data[0]['id']
                logger.info(f"✅ Newsletter created with ID: {newsletter_id}")
                return newsletter_id
            else:
                logger.error("❌ Failed to create newsletter: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to create newsletter: {str(e)}")
            return None
    
    def get_newsletter(self, newsletter_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a newsletter by ID.
        
        Args:
            newsletter_id: ID of the newsletter to retrieve
            
        Returns:
            dict: Newsletter data if found, None otherwise
        """
        try:
            response = self.supabase.table('newsletters').select('*').eq('id', newsletter_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                logger.warning(f"Newsletter with ID {newsletter_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve newsletter: {str(e)}")
            return None
    
    def get_user_clients(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all clients for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            list: List of client data
        """
        try:
            response = self.supabase.table('clients').select('*').eq('user_id', user_id).execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve clients: {str(e)}")
            return []
    
    def add_newsletter_recipients(self, newsletter_id: str, client_ids: List[str]) -> bool:
        """
        Add recipients to a newsletter.
        
        Args:
            newsletter_id: ID of the newsletter
            client_ids: List of client IDs to add as recipients
            
        Returns:
            bool: True if recipients were added successfully, False otherwise
        """
        try:
            recipients_data = [
                {
                    'newsletter_id': newsletter_id,
                    'client_id': client_id,
                    'sent': False,
                    'sent_at': None
                }
                for client_id in client_ids
            ]
            
            response = self.supabase.table('newsletter_recipients').insert(recipients_data).execute()
            
            if response.data:
                logger.info(f"✅ Added {len(client_ids)} recipients to newsletter {newsletter_id}")
                return True
            else:
                logger.error("❌ Failed to add recipients: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to add recipients: {str(e)}")
            return False
    
    def send_newsletter(self, newsletter_id: str, test_mode: bool = False) -> Dict[str, Any]:
        """
        Send a newsletter to all its recipients.
        
        Args:
            newsletter_id: ID of the newsletter to send
            test_mode: If True, only log what would be sent without actually sending
            
        Returns:
            dict: Summary of the sending operation
        """
        try:
            # Get newsletter data
            newsletter = self.get_newsletter(newsletter_id)
            if not newsletter:
                return {'success': False, 'error': 'Newsletter not found'}
            
            # Get recipients
            recipients_response = self.supabase.table('newsletter_recipients')\
                .select('*, clients(name, email)')\
                .eq('newsletter_id', newsletter_id)\
                .eq('sent', False)\
                .execute()
            
            if not recipients_response.data:
                return {'success': False, 'error': 'No unsent recipients found'}
            
            recipients = recipients_response.data
            sent_count = 0
            failed_count = 0
            errors = []
            
            for recipient in recipients:
                client = recipient['clients']
                if not client or not client.get('email'):
                    logger.warning(f"Skipping recipient {recipient['id']}: No email address")
                    continue
                
                client_email = client['email']
                client_name = client.get('name', 'Valued Client')
                
                # Personalize the content
                personalized_content = newsletter['content'].replace(
                    '{{client_name}}', client_name
                )
                
                if test_mode:
                    logger.info(f"TEST MODE: Would send to {client_email}")
                    sent_count += 1
                else:
                    # Send the email
                    success = self.send_email(
                        to_email=client_email,
                        subject=newsletter['title'],
                        html_content=personalized_content
                    )
                    
                    if success:
                        # Mark as sent in database
                        self.supabase.table('newsletter_recipients')\
                            .update({
                                'sent': True,
                                'sent_at': datetime.now(timezone.utc).isoformat()
                            })\
                            .eq('id', recipient['id'])\
                            .execute()
                        sent_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"Failed to send to {client_email}")
            
            # Update newsletter status
            if not test_mode and sent_count > 0:
                self.supabase.table('newsletters')\
                    .update({
                        'status': 'sent' if failed_count == 0 else 'partially_sent',
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    })\
                    .eq('id', newsletter_id)\
                    .execute()
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'errors': errors,
                'test_mode': test_mode
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send newsletter: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_and_send_newsletter(self, user_id: str, title: str, content: str, 
                                 client_ids: Optional[List[str]] = None,
                                 test_mode: bool = False) -> Dict[str, Any]:
        """
        Create a newsletter and send it to specified clients or all user clients.
        
        Args:
            user_id: ID of the user creating the newsletter
            title: Newsletter title
            content: Newsletter HTML content
            client_ids: List of specific client IDs to send to (optional)
            test_mode: If True, only log what would be sent
            
        Returns:
            dict: Summary of the operation
        """
        try:
            # Create newsletter
            newsletter_id = self.create_newsletter(user_id, title, content)
            if not newsletter_id:
                return {'success': False, 'error': 'Failed to create newsletter'}
            
            # Get client IDs if not provided
            if client_ids is None:
                clients = self.get_user_clients(user_id)
                client_ids = [client['id'] for client in clients]
            
            if not client_ids:
                return {'success': False, 'error': 'No clients found to send to'}
            
            # Add recipients
            if not self.add_newsletter_recipients(newsletter_id, client_ids):
                return {'success': False, 'error': 'Failed to add recipients'}
            
            # Send newsletter
            result = self.send_newsletter(newsletter_id, test_mode)
            result['newsletter_id'] = newsletter_id
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to create and send newsletter: {str(e)}")
            return {'success': False, 'error': str(e)}


def main():
    """Example usage of the email service."""
    try:
        email_service = EmailService()
        
        # Example: Create and send a test newsletter
        user_id = "your-user-id-here"  # Replace with actual user ID
        title = "CreatorPulse Daily Report"
        content = """
        <html>
        <body>
            <h1>Hello {{client_name}}!</h1>
            <p>Here's your daily CreatorPulse report.</p>
            <p>Best regards,<br>The CreatorPulse Team</p>
        </body>
        </html>
        """
        
        result = email_service.create_and_send_newsletter(
            user_id=user_id,
            title=title,
            content=content,
            test_mode=True  # Set to False to actually send emails
        )
        
        print(f"Newsletter operation result: {result}")
        
    except Exception as e:
        logger.error(f"❌ Error in main: {str(e)}")


if __name__ == "__main__":
    main()
