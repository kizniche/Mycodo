# coding=utf-8
import email
import logging
import smtplib
import socket

import os

from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import set_user_grp

logger = logging.getLogger("mycodo.notification")


#
# Email notification
#

def send_email(smtp_host, smtp_ssl, smtp_port, smtp_user, smtp_pass,
               smtp_email_from, email_to, message,
               attachment_file=False, attachment_type=False):
    """
    Email a specific recipient or recipients a message.

    :param smtp_host: Email server hostname
    :type smtp_host: str
    :param smtp_ssl: Use SSL?
    :type smtp_ssl: bool
    :param smtp_port: Email server port
    :type smtp_port: int
    :param smtp_user: Email server user name
    :type smtp_user: str
    :param smtp_pass: Email server password
    :type smtp_pass: str
    :param smtp_email_from: From email address
    :type smtp_email_from: str
    :param email_to: To email address(s)
    :type email_to: str or list
    :param message: Message in the body of the email
    :type message: unicode
    :param attachment_file: location of file attachment
    :type attachment_file: str
    :param attachment_type: type of attachment ('still' or 'video')
    :type attachment_type: str

    :return: success (0) or failure (1)
    :rtype: bool
    """
    try:
        if smtp_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.ehlo()
            server.starttls()
        server.login(smtp_user, smtp_pass)
        msg = email.mime.multipart.MIMEMultipart()
        msg['Subject'] = "Mycodo Notification ({})".format(
            socket.gethostname())
        msg['From'] = smtp_email_from
        msg['To'] = email_to
        msg_body = email.mime.text.MIMEText(message.encode('utf-8'), 'plain', 'utf-8')
        msg.attach(msg_body)

        if attachment_file and attachment_type == 'still':
            img_data = open(attachment_file, 'rb').read()
            image = email.mime.image.MIMEImage(img_data,
                              name=os.path.basename(attachment_file))
            msg.attach(image)
        elif attachment_file and attachment_type == 'video':
            out_filename = '{}-compressed.h264'.format(attachment_file)
            cmd_output(
                'avconv -i "{}" -vf scale=-1:768 -c:v libx264 -preset '
                'veryfast -crf 22 -c:a copy "{}"'.format(
                    attachment_file, out_filename))
            set_user_grp(out_filename, 'mycodo', 'mycodo')
            f = open(attachment_file, 'rb').read()
            video = email.mime.base.MIMEBase('application', 'octet-stream')
            video.set_payload(f)
            email.encoders.encode_base64(video)
            video.add_header('Content-Disposition',
                             'attachment; filename="{}"'.format(
                                 os.path.basename(attachment_file)))
            msg.attach(video)

        server.sendmail(msg['From'], msg['To'].split(","), msg.as_string())
        server.quit()
        return 0
    except Exception as error:
        if logging:
            logging.exception(
                "Could not send email to {add} with message: {msg}. Error: "
                "{err}".format(add=email_to, msg=message, err=error))
        return 1
