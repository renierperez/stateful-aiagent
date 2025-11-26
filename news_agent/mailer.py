import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

def send_email(user_email, user_password, subject, body, to_email=None, bcc_emails=None, is_html=False):
    """
    Sends an email using Gmail SMTP.
    """
    if to_email is None:
        to_email = user_email
        
    logging.info(f"Sending email to {to_email} (BCC: {bcc_emails})...")
    
    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    mime_type = 'html' if is_html else 'plain'
    msg.attach(MIMEText(body, mime_type, 'utf-8'))
    
    # Prepare list of all recipients for SMTP
    all_recipients = [to_email]
    if bcc_emails:
        if isinstance(bcc_emails, str):
            all_recipients.append(bcc_emails)
        else:
            all_recipients.extend(bcc_emails)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user_email, user_password)
        server.sendmail(user_email, all_recipients, msg.as_string())
        server.quit()
        logging.info("Email sent successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False
