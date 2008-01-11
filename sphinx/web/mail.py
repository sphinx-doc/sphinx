# -*- coding: utf-8 -*-
"""
    sphinx.web.mail
    ~~~~~~~~~~~~~~~

    A simple module for sending e-mails, based on simplemail.py.

    :copyright: 2004-2007 by Gerold Penz.
    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import os.path
import sys
import time
import smtplib
import mimetypes

from email import Encoders
from email.Header import Header
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formataddr
from email.Utils import formatdate
from email.Message import Message
from email.MIMEAudio import MIMEAudio
from email.MIMEBase import MIMEBase
from email.MIMEImage import MIMEImage



# Exceptions
#----------------------------------------------------------------------
class SimpleMail_Exception(Exception):
    def __str__(self):
        return self.__doc__

class NoFromAddress_Exception(SimpleMail_Exception):
    pass

class NoToAddress_Exception(SimpleMail_Exception):
    pass

class NoSubject_Exception(SimpleMail_Exception):
    pass

class AttachmentNotFound_Exception(SimpleMail_Exception):
    pass


class Attachments(object):
    def __init__(self):
        self._attachments = []

    def add_filename(self, filename = ''):
        self._attachments.append(('file', filename))

    def add_string(self, filename, text, mimetype):
        self._attachments.append(('string', (filename, text, mimetype)))

    def count(self):
        return len(self._attachments)

    def get_list(self):
        return self._attachments


class Recipients(object):
    def __init__(self):
        self._recipients = []

    def add(self, address, caption = ''):
        self._recipients.append(formataddr((caption, address)))

    def count(self):
        return len(self._recipients)

    def __repr__(self):
        return str(self._recipients)

    def get_list(self):
        return self._recipients


class CCRecipients(Recipients):
    pass


class BCCRecipients(Recipients):
    pass


class Email(object):

    def __init__(
        self,
        from_address = "",
        from_caption = "",
        to_address = "",
        to_caption = "",
        subject = "",
        message = "",
        smtp_server = "localhost",
        smtp_user = "",
        smtp_password = "",
        user_agent = "",
        reply_to_address = "",
        reply_to_caption = "",
        use_tls = False,
    ):
        """
        Initialize the email object
            from_address     = the email address of the sender
            from_caption     = the caption (name) of the sender
            to_address       = the email address of the recipient
            to_caption       = the caption (name) of the recipient
            subject          = the subject of the email message
            message          = the body text of the email message
            smtp_server      = the ip-address or the name of the SMTP-server
            smtp_user        = (optional) Login name for the SMTP-Server
            smtp_password    = (optional) Password for the SMTP-Server
            user_agent       = (optional) program identification
            reply_to_address = (optional) Reply-to email address
            reply_to_caption = (optional) Reply-to caption (name)
            use_tls          = (optional) True, if the connection should use TLS
                               to encrypt.
        """

        self.from_address = from_address
        self.from_caption = from_caption
        self.recipients = Recipients()
        self.cc_recipients = CCRecipients()
        self.bcc_recipients = BCCRecipients()
        if to_address:
            self.recipients.add(to_address, to_caption)
        self.subject = subject
        self.message = message
        self.smtp_server = smtp_server
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.attachments = Attachments()
        self.content_subtype = "plain"
        self.content_charset = "iso-8859-1"
        self.header_charset = "us-ascii"
        self.statusdict = None
        self.user_agent = user_agent
        self.reply_to_address = reply_to_address
        self.reply_to_caption = reply_to_caption
        self.use_tls = use_tls


    def send(self):
        """
        Send the mail. Returns True if successfully sent to at least one
        recipient.
        """

        # validation
        if len(self.from_address.strip()) == 0:
            raise NoFromAddress_Exception
        if self.recipients.count() == 0:
            if (
                (self.cc_recipients.count() == 0) and
                (self.bcc_recipients.count() == 0)
            ):
                raise NoToAddress_Exception
        if len(self.subject.strip()) == 0:
            raise NoSubject_Exception

        # assemble
        if self.attachments.count() == 0:
            msg = MIMEText(
                _text = self.message,
                _subtype = self.content_subtype,
                _charset = self.content_charset
            )
        else:
            msg = MIMEMultipart()
            if self.message:
                att = MIMEText(
                    _text = self.message,
                    _subtype = self.content_subtype,
                    _charset = self.content_charset
                )
                msg.attach(att)

        # add headers
        from_str = formataddr((self.from_caption, self.from_address))
        msg["From"] = from_str
        if self.reply_to_address:
            reply_to_str = formataddr((self.reply_to_caption, self.reply_to_address))
            msg["Reply-To"] = reply_to_str
        if self.recipients.count() > 0:
            msg["To"] = ", ".join(self.recipients.get_list())
        if self.cc_recipients.count() > 0:
            msg["Cc"] = ", ".join(self.cc_recipients.get_list())
        msg["Date"] = formatdate(time.time())
        msg["User-Agent"] = self.user_agent
        try:
            msg["Subject"] = Header(
                self.subject, self.header_charset
            )
        except(UnicodeDecodeError):
            msg["Subject"] = Header(
                self.subject, self.content_charset
            )
        msg.preamble = "You will not see this in a MIME-aware mail reader.\n"
        msg.epilogue = ""

        # assemble multipart
        if self.attachments.count() > 0:
            for typ, info in self.attachments.get_list():
                if typ == 'file':
                    filename = info
                    if not os.path.isfile(filename):
                        raise AttachmentNotFound_Exception, filename
                    mimetype, encoding = mimetypes.guess_type(filename)
                    if mimetype is None or encoding is not None:
                        mimetype = 'application/octet-stream'
                    if mimetype.startswith('text/'):
                        fp = file(filename)
                    else:
                        fp = file(filename, 'rb')
                    text = fp.read()
                    fp.close()
                else:
                    filename, text, mimetype = info
                maintype, subtype = mimetype.split('/', 1)
                if maintype == 'text':
                    # Note: we should handle calculating the charset
                    att = MIMEText(text, _subtype=subtype)
                elif maintype == 'image':
                    att = MIMEImage(text, _subtype=subtype)
                elif maintype == 'audio':
                    att = MIMEAudio(text, _subtype=subtype)
                else:
                    att = MIMEBase(maintype, subtype)
                    att.set_payload(text)
                    # Encode the payload using Base64
                    Encoders.encode_base64(att)
                # Set the filename parameter
                att.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename = os.path.basename(filename).strip()
                )
                msg.attach(att)

        # connect to server
        smtp = smtplib.SMTP()
        if self.smtp_server:
            smtp.connect(self.smtp_server)
        else:
            smtp.connect()

        # TLS?
        if self.use_tls:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

        # authenticate
        if self.smtp_user:
            smtp.login(user = self.smtp_user, password = self.smtp_password)

        # send
        self.statusdict = smtp.sendmail(
            from_str,
            (
                self.recipients.get_list() +
                self.cc_recipients.get_list() +
                self.bcc_recipients.get_list()
            ),
            msg.as_string()
        )
        smtp.close()

        return True
