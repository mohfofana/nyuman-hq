import adapters.common.ports.out.smtp_mail_sender as module
from adapters.common.ports.out.smtp_mail_sender import SmtpMailSender


class FakeSmtp:
    instances: list["FakeSmtp"] = []

    def __init__(self, host, port, context=None, timeout=None):
        self.host, self.port, self.calls = host, port, []
        FakeSmtp.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self, context=None):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(("login", user))

    def send_message(self, message):
        self.calls.append(("send", message["From"], message["To"], message["Subject"]))


def test_sans_reglages_l_envoi_est_ferme():
    assert not SmtpMailSender(None, 465, None, None, None).configured
    assert not SmtpMailSender("mail.example.com", 465, "hq@example.com", None, None).configured


async def test_envoi_ssl_sur_le_port_465(monkeypatch):
    FakeSmtp.instances.clear()
    monkeypatch.setattr(module.smtplib, "SMTP_SSL", FakeSmtp)
    sender = SmtpMailSender("mail.example.com", 465, "hq@example.com", "mot-de-passe-de-test", None)
    assert sender.configured

    await sender.send("awa@example.com", "Sujet", "texte", "<p>texte</p>")

    smtp = FakeSmtp.instances[0]
    assert (smtp.host, smtp.port) == ("mail.example.com", 465)
    assert smtp.calls == [("login", "hq@example.com"), ("send", "Nyuman HQ <hq@example.com>", "awa@example.com", "Sujet")]


async def test_envoi_starttls_sur_le_port_587(monkeypatch):
    FakeSmtp.instances.clear()
    monkeypatch.setattr(module.smtplib, "SMTP", FakeSmtp)
    sender = SmtpMailSender("mail.example.com", 587, "hq@example.com", "mot-de-passe-de-test", "equipe@example.com")

    await sender.send("awa@example.com", "Sujet", "texte", "<p>texte</p>")

    assert FakeSmtp.instances[0].calls[0] == "starttls"
    assert FakeSmtp.instances[0].calls[2][1] == "Nyuman HQ <equipe@example.com>"
