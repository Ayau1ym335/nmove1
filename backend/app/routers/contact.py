from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import get_settings

router = APIRouter(prefix="/api", tags=["contact"])

settings = get_settings()


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    form_type: str  # "patient" or "clinician"
    message: str = ""
    organization: str = ""


@router.post("/contact")
async def submit_contact_form(request: ContactRequest):
    """
    Handle contact form submissions and send email notification.
    """
    try:
        # Create email content
        subject = f"NMove Contact Form - {request.form_type.capitalize()}"
        
        body = f"""
New contact form submission from NMove website:

Type: {request.form_type.capitalize()}
Name: {request.name}
Email: {request.email}
Organization: {request.organization if request.organization else "N/A"}

Message:
{request.message if request.message else "No message provided"}

---
This is an automated message from the NMove contact form.
"""

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.MAIL_USERNAME
        msg['To'] = settings.MAIL_USERNAME  # Send to self
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email via Gmail SMTP
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)

        return {
            "success": True,
            "message": "Your message has been sent successfully!"
        }

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Email authentication failed. Please check server configuration."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )
