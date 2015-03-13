import smtplib
from common.settings import MAIL_SERVER, MAIL_TARGETS
class MailSender(object):
    def __init__(self):
        self._buff = []

    def append(self, msg):
        pass

    def send_one(self, content, target=[]):
        msg = MIMEText('hello, this is a test html <b>haha</b>', 'html','utf8')
        msg.set_charset('utf8')
        msg['Subject'] = 'The contents of 中文标题'
        me = MAIL_SERVER['src']
        msg['From'] = me
        msg['To'] = target
        s = smtplib.SMTP(MAIL_SERVER['server'], target, msg.as_string())
        s.quit()

        

