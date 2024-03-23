from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional
import aiofiles
from fastapi import Request
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import jwt
from configs.auth import ALGORITHM, SECRET
from configs.emails import EMAIL_HOST_PASSWORD, EMAIL_HOST_USER, EMAIL_HOST_USERNAME
from pathlib import Path


class EmailSender(ABC):
    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME=EMAIL_HOST_USERNAME,
            MAIL_PASSWORD=EMAIL_HOST_PASSWORD,
            MAIL_FROM=EMAIL_HOST_USER,
            MAIL_PORT=587,
            MAIL_SERVER="smtp.gmail.com",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )

    async def load_template(self, template_name):
        """
        Load the email template from the file system based on the template name.
        """
        template_path = Path(__file__).parent.parent / f"templates/{template_name}"
        with open(template_path, "r") as f:
            template = f.read()
        return template

    @abstractmethod
    async def prepare_email_data(self, user, request, template):
        """
        Prepare the data required for the email template.
        This must be implemented by each subclass.
        """
        pass

    async def send_email(self, recipients, request: Optional[Request], template_name):
        """
        Send an email to multiple recipients.
        recipients: List of email addresses.
        """
        # Load the email template based on the file name.
        base_template = await self.load_template(template_name)
        # Assuming we don't need to prepare the data differently for each recipient.
        # This method might need adjustments if that's not the case.
        prepared_template = base_template  # Directly use the loaded template for simplicity.

        # Create a message schema for each recipient and send the email.
        for email in recipients:
            message = MessageSchema(
                subject=self.subject,  # Utilizing subject defined in the subclass
                recipients=[email],  # Send to the current recipient.
                body=prepared_template,
                subtype="html",
            )
            fm = FastMail(self.config)
            await fm.send_message(message)

class VerificationEmailSender(EmailSender):

    template_name = "send-verification.html"
    subject = "Verify Your Email Address"

    async def prepare_email_data(self, user, request, template):
        token_data = {
            "user_id": str(user.id),
            "username": user.username,
        }
        token = jwt.encode(token_data, SECRET, algorithm=ALGORITHM)

        domain = str(request.base_url)
        path = request.url.path.replace("signup", "verification")[1:]

        url = f"{domain}{path}?token={token}"
        prepared_template = template.replace(
            'href="url"', f'href="{url}"'
        )  # Correct replacement for the actual href

        return prepared_template


class ResetPasswordEmailSender(EmailSender):
    template_name = "password-reset.html"
    subject = "Password Reset"

    async def prepare_email_data(self, user, request, template):
        # Current time
        current_time = datetime.now()
        # Token expiration time: current time + 10 minutes
        exp_time = current_time + timedelta(minutes=10)

        token_data = {
            "user_id": str(user.id),
            "username": user.username,
            "exp": exp_time.timestamp(),  # Add expiration time to the token data
        }

        token = jwt.encode(token_data, SECRET, algorithm=ALGORITHM)

        domain = str(request.base_url)
        path = request.url.path.replace("password-forgot", "password-reset")[1:]

        url = f"{domain}{path}?token={token}"
        prepared_template = template.replace(
            'href="url"', f'href="{url}"'
        )  # Correct replacement for the actual href
        return prepared_template


class ReportEmailSender(EmailSender):
    subject = "ALX Report"

    async def load_template(self, file_name):
        """
        Load the email template from the file system based on the file name.
        """
        template_path = Path(__file__).parent.parent / f"reports/{file_name}"
        async with aiofiles.open(template_path, "r") as f:
            template = await f.read()
        return template

    async def prepare_email_data(self, user, request, template):
        """
        For report emails, we might not need to prepare data in the same way as other emails.
        This method could be customized based on your requirements for report emails.
        """
        # Example: Directly return the template without modification.
        # You might want to customize this based on your needs.
        return template

    

verify_email_sender = VerificationEmailSender()

reset_email_sender = ResetPasswordEmailSender()

report_email_sender = ReportEmailSender()
