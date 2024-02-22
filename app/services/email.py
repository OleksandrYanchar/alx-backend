from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import jwt
from configs.auth import ALGORITHM, SECRET
from configs.emails import EMAIL_HOST_PASSWORD, EMAIL_HOST_USER, EMAIL_HOST_USERNAME
from models.users import Users
from schemas.email import EmailSchema
from pathlib import Path

config = ConnectionConfig (
    MAIL_USERNAME = EMAIL_HOST_USERNAME,
    MAIL_PASSWORD = EMAIL_HOST_PASSWORD ,
    MAIL_FROM  = EMAIL_HOST_USER ,
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_email(email: EmailSchema, user: Users):
    token_data = {
        'user_id': str(user.id),  # Adjusting to match the verify_token expectations
        'username': user.username,
    }
    
    token = jwt.encode(token_data, SECRET, algorithm=ALGORITHM)

    template_path = Path(__file__).parent.parent / 'templates/send-verivication.html'
    with open(template_path, 'r') as f:
        template = f.read()

    template = template.replace("{{token}}", token)

    # Assuming email_schema.email is a list and you want to send email to the first address in the list

    message = MessageSchema(
        subject='Email Verification',
        recipients=email,  # This is now a list, as expected by MessageSchema
        body=template,
        subtype='html',
    )

    fm = FastMail(config)
    print(token)
    await fm.send_message(message)