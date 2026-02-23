import shutil
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def zip_and_email(folder_path: str, student_email: str):
    # Create zip file
    zip_path = shutil.make_archive(folder_path, 'zip', folder_path)
    
    # Email setup
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = student_email
    msg['Subject'] = "Your COS201 ML Assignment Solution"
    
    body = "Hey! Attached is your unique dataset, personalized Python script, and your generated plots. Read the defense guide just in case the lecturer asks questions."
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach zip file
    with open(zip_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(zip_path)}')
        msg.attach(part)
    
    # Send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    
    # Cleanup
    shutil.rmtree(folder_path)
    os.remove(zip_path)
