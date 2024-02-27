from abc import ABC, abstractmethod
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

    async def send_email(self, user, request):
        """
        Send an email using the prepared data.
        """
        # Utilizing template_name defined in the subclass
        base_template = await self.load_template(self.template_name)
        prepared_template = await self.prepare_email_data(user, request, base_template)
        
        message = MessageSchema(
            subject=self.subject,  # Utilizing subject defined in the subclass
            recipients=[user.email],  # Assuming 'email' attribute in 'user'
            body=prepared_template,
            subtype="html",
        )
        
        fm = FastMail(self.config)
        await fm.send_message(message)
        
        
class VerificationEmailSender(EmailSender):
    
    template_name = 'send-verification.html'
    subject = "Verify Your Email Address"
    
    async def prepare_email_data(self, user, request, template):
        token_data = {
            "user_id": str(user.id),
            "username": user.username,
        }
        token = jwt.encode(token_data, SECRET, algorithm=ALGORITHM)
        
        domain = str(request.base_url)
        path = request.url.path.replace('signup', 'verification')[1:]
        
        url = f'{domain}{path}?token={token}'
        prepared_template = template.replace("href=\"url\"", f"href=\"{url}\"")  # Correct replacement for the actual href
        
        return prepared_template
    
class ResetPasswordEmailSender(EmailSender):
    
    template_name = 'send-verification.html'
    subject = "Verify Your Email Address"
    
    async def prepare_email_data(self, user, request, template):
        token_data = {
            "user_id": str(user.id),
            "username": user.username,
        }
        token = jwt.encode(token_data, SECRET, algorithm=ALGORITHM)
        
        domain = str(request.base_url)
        path = request.url.path.replace('signup', 'verification')[1:]
        
        url = f'{domain}{path}?token={token}'
        prepared_template = template.replace("href=\"url\"", f"href=\"{url}\"")  # Correct replacement for the actual href
        
        return prepared_template