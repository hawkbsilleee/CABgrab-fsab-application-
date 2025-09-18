import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os 

load_dotenv()

def send_email(crn, to_email):
    from_email = os.getenv("EMAIL_ADDRESS")
    app_password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = "CABgrab: A seat you're tracking has opened up!"
    msg.attach(MIMEText(f"Hi! This is Ethan and Dhruv from CABgrab. \n\nA seat in {crn} has opened up. Hurry to CAB to grab it!", "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls() 
        server.login(from_email, app_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    send_email("123", "ethan_seiz@brown.edu")