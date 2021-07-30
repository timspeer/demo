'''send_mail'''
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import base64

from password_encryption import get_password

def send_email(text:str, subject:str, senders:list=None,
               username:str="#REMOVED#",
               text_format:str="plain"):
    '''send an email'''
    password:str = get_password(username, "Email")
    if not senders:
        senders = ["#REMOVED#"]
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    msg = MIMEMultipart()
    msg['From'] = "#REMOVED#"
    msg["To"] = "; ".join(senders)
    msg["Subject"] =  subject
    part = MIMEText(str(text), text_format)
    msg.attach(part)
    server.sendmail(username, senders, msg.as_string())

def send_with_attachment(text:str, subject:str, filename:os.PathLike, senders:list=None,
                         username:str="#REMOVED#"):
    '''send email with attachment'''
    password:str = get_password(username, "Email")
    if not senders:
        senders = ["#REMOVED#", "#REMOVED#"]
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    msg = MIMEMultipart()
    msg['From'] = "#REMOVED#"
    msg["To"] = "; ".join(senders)
    msg["Subject"] = subject
    text_part = MIMEText(str(text), "plain")
    msg.attach(text_part)
    part = MIMEBase("application", "pdf")
    part.add_header('Content-Transfer-Encoding', 'base64')
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    filepath = open(filename, 'rb')
    part.set_payload(str(base64.encodebytes(filepath.read()), 'ascii'))
    filepath.close()
    msg.attach(part)
    server.sendmail(username, senders, msg.as_string())