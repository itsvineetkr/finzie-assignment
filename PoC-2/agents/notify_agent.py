import os
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from utils.prompts import NOTIFICATION_EMAIL_TEMPLATE, NOTIFICATION_SMS_TEMPLATE
from models.database import Notification
from schemas.models import NotificationStatus
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio


try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient

    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


class NotifyAgent(BaseAgent):
    def __init__(self, db_session: AsyncSession):
        super().__init__("NotifyAgent")
        self.db_session = db_session

        # Initialize SendGrid
        self.sendgrid_client = None
        self.sendgrid_from_email = None
        if SENDGRID_AVAILABLE:
            api_key = os.getenv("SENDGRID_API_KEY")
            if api_key:
                try:
                    self.sendgrid_client = SendGridAPIClient(api_key)
                    self.sendgrid_from_email = os.getenv("SENDGRID_FROM_EMAIL")
                    self.logger.info("SendGrid client initialized")
                except Exception as e:
                    self.logger.error(f"Failed to initialize SendGrid: {e}")

        # Initialize Twilio
        self.twilio_client = None
        self.twilio_phone = None
        if TWILIO_AVAILABLE:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            if account_sid and auth_token:
                try:
                    self.twilio_client = TwilioClient(account_sid, auth_token)
                    self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
                    self.logger.info("Twilio client initialized")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Twilio: {e}")

    async def process(
        self, message: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process notification request"""
        try:
            if not context:
                raise ValueError("Context required for notifications")

            notification_type = context.get("notification_type", "email")
            recipient_email = context.get("recipient_email")
            recipient_phone = context.get("recipient_phone")
            ticket_number = context.get("ticket_number", "N/A")

            # Create notification record
            notification = await self._create_notification_record(
                message,
                notification_type,
                recipient_email,
                recipient_phone,
                context.get("session_id"),
                context.get("ticket_id"),
            )

            success = False
            error_message = None

            if notification_type == "email" and recipient_email:
                success, error_message = await self._send_email(
                    recipient_email, message, ticket_number
                )
            elif notification_type in ["sms", "whatsapp"] and recipient_phone:
                success, error_message = await self._send_sms(
                    recipient_phone, message, ticket_number, notification_type
                )
            else:
                error_message = f"Invalid notification type or missing recipient info"

            # Update notification status
            await self._update_notification_status(notification, success, error_message)

            result = {
                "notification_sent": success,
                "notification_type": notification_type,
                "notification_id": notification.id,
                "agent": self.name,
            }

            if error_message:
                result["error"] = error_message

            self.log_interaction(f"Notification request: {notification_type}", result)
            return result

        except Exception as e:
            self.logger.error(f"Error in notification processing: {e}")
            return {"notification_sent": False, "agent": self.name, "error": str(e)}

    async def _create_notification_record(
        self,
        message: str,
        notification_type: str,
        recipient_email: Optional[str],
        recipient_phone: Optional[str],
        session_id: Optional[str],
        ticket_id: Optional[int],
    ) -> Notification:
        """Create a notification record in the database"""
        notification = Notification(
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            message=message,
            notification_type=notification_type,
            status=NotificationStatus.PENDING,
            session_id=session_id,
            ticket_id=ticket_id,
        )

        self.db_session.add(notification)
        await self.db_session.commit()
        await self.db_session.refresh(notification)

        return notification

    async def _send_email(
        self, recipient: str, message: str, ticket_number: str
    ) -> tuple:
        """Send email notification"""
        if not self.sendgrid_client:
            return False, "SendGrid not configured"

        try:
            subject = f"Support Ticket Update - {ticket_number}"
            formatted_message = NOTIFICATION_EMAIL_TEMPLATE.format(
                subject=subject, message=message, ticket_number=ticket_number
            )

            mail = Mail(
                from_email=self.sendgrid_from_email,
                to_emails=recipient,
                subject=subject,
                html_content=formatted_message.replace("\n", "<br>"),
            )

            response = self.sendgrid_client.send(mail)

            if response.status_code in [200, 201, 202]:
                return True, None
            else:
                return False, f"SendGrid error: {response.status_code}"

        except Exception as e:
            return False, f"Email sending failed: {str(e)}"

    async def _send_sms(
        self, recipient: str, message: str, ticket_number: str, notification_type: str
    ) -> tuple:
        """Send SMS or WhatsApp notification"""
        if not self.twilio_client:
            return False, "Twilio not configured"

        try:
            formatted_message = NOTIFICATION_SMS_TEMPLATE.format(
                message=message, ticket_number=ticket_number
            )

            # Determine the messaging service
            if notification_type == "whatsapp":
                from_number = f"whatsapp:{self.twilio_phone}"
                to_number = f"whatsapp:{recipient}"
            else:
                from_number = self.twilio_phone
                to_number = recipient

            message_obj = self.twilio_client.messages.create(
                body=formatted_message, from_=from_number, to=to_number
            )

            return True, None

        except Exception as e:
            return False, f"SMS/WhatsApp sending failed: {str(e)}"

    async def _update_notification_status(
        self, notification: Notification, success: bool, error_message: Optional[str]
    ):
        """Update notification status in database"""
        try:
            notification.status = (
                NotificationStatus.SENT if success else NotificationStatus.FAILED
            )
            if error_message:
                notification.error_message = error_message

            await self.db_session.commit()

        except Exception as e:
            self.logger.error(f"Failed to update notification status: {e}")

    def get_notification_capabilities(self) -> Dict[str, bool]:
        """Return available notification capabilities"""
        return {
            "email": self.sendgrid_client is not None,
            "sms": self.twilio_client is not None,
            "whatsapp": self.twilio_client is not None,
        }
