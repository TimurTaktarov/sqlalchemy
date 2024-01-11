import os
import smtplib
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from settings import settings


def send_email(
    *,
    recipients: list[str],
    mail_body: str,
    mail_subject: str,
    attachment: str = None,
    mime_type: str = "html",
):
    SERVER = settings.SMTP_SERVER
    PASSWORD = settings.EMAIL_TOKEN
    USER = settings.EMAIL_USER

    msg = MIMEMultipart("alternative")
    msg["Subject"] = mail_subject
    msg["From"] = f"<Your {USER}>"
    msg["To"] = ", ".join(recipients)
    msg["Reply-To"] = USER
    msg["Return-Path"] = USER
    msg["X-Mailer"] = "decorator"

    if attachment:
        file_exists = os.path.exists(attachment)
        if not file_exists:
            print(f"file {attachment} does not exist")
        else:
            basename = os.path.basename(attachment)
            filesize = os.path.getsize(attachment)
            file = MIMEBase("application", f"octet-stream; name={basename}")
            file.set_payload(open(attachment, "rb").read())
            file.add_header("Content-Description", attachment)
            file.add_header("Content-Description", f"attachment; filename={attachment}; size={filesize}")
            encoders.encode_base64(file)
            msg.attach(file)

    text_to_send = MIMEText(
        mail_body, mime_type
    )  # plain, html, image, audio, video https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
    msg.attach(text_to_send)

    mail = smtplib.SMTP_SSL(SERVER)
    mail.login(USER, PASSWORD)
    mail.sendmail(USER, recipients, msg.as_string())
    mail.quit()


def send_email_verification(user_email, user_uuid, user_name, host: str = "http://127.0.0.1:8000/"):
    activate_url = f'{host}api/user/verify/{user_uuid}'

    with open(
            Path(__file__).parent / 'email_verification.html',
            encoding='utf-8') as file:
        content = file.read()
        content = content\
            .replace('{{ user }}', user_name)\
            .replace('{{ link }}', activate_url)

    send_email(
        recipients=[user_email],
        mail_body=content,
        mail_subject=f'Account verification'
    )