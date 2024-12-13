from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr
from email.mime.text import MIMEText
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

router = APIRouter()

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')

templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

class EmailRequest(BaseModel):
    to_email: EmailStr
    otp: str

def get_credentials():
    token_uri = 'https://oauth2.googleapis.com/token'
    credentials = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri=token_uri,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/gmail.send']
    )
    return credentials

def send_email_via_gmail_api(to_email, subject, body):
    credentials = get_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    message = MIMEText(body,"html")
    message['to'] = to_email
    message['from'] = 'me'
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message = {'raw': raw_message}
    sent_message = service.users().messages().send(userId='me', body=message).execute()
    return sent_message

@router.post("/send")
async def send_email(email_request: EmailRequest, x_action: str = Header(None)):
    print(REFRESH_TOKEN)
    if x_action not in ["registration", "login"]:
        raise HTTPException(status_code=400, detail="Invalid action header")
    to_email = email_request.to_email
    otp = email_request.otp

    subject = f"Your OTP for {x_action.capitalize()}"

    # Load and render appropriate template
    try:
        template = env.get_template(f"{x_action}.html")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template error: {e}")

    body = template.render(otp=otp)

    try:
        send_email_via_gmail_api(to_email, subject, body)
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {e}")
