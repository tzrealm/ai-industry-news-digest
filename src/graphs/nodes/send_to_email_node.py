import datetime
import json
import smtplib
import ssl

from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

from cozeloop.decorator import observe
from coze_workload_identity import Client
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import SendEmailInput, SendEmailOutput


def _get_email_config() -> dict:
    """获取邮件集成配置（自动读取环境变量，无需手动设置）。"""
    client = Client()
    credential = client.get_integration_credential("integration-email-imap-smtp")
    if isinstance(credential, (str, bytes)):
        return json.loads(credential)
    return dict(credential)


@observe
def _send_plain_email(subject: str, content: str, to_addrs):
    """发送纯文本邮件，返回发送结果字典。"""
    cfg = _get_email_config()
    account = cfg.get("account", "")

    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = formataddr(("AI新闻早报", account))
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = Header(subject, "utf-8")
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()

    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    with smtplib.SMTP_SSL(
        cfg["smtp_server"], cfg["smtp_port"], context=ctx, timeout=30
    ) as server:
        server.ehlo()
        server.login(account, cfg["auth_code"])
        server.sendmail(account, to_addrs, msg.as_string())
        server.quit()

    return {"status": "success", "recipient_count": len(to_addrs)}


def send_to_email_node(
    state: SendEmailInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> SendEmailOutput:
    """
    title: 发送至邮箱
    desc: 将生成的 AI 行业要闻日报通过邮件发送给用户
    integrations: 邮件
    """
    ctx = runtime.context  # noqa: F841

    email_config = _get_email_config()
    account = email_config.get("account", "")
    if not account:
        return SendEmailOutput(send_result="邮箱账号未配置，无法发送")

    subject = f"AI 行业要闻早报 · {datetime.date.today().isoformat()}"
    try:
        result = _send_plain_email(subject, state.digest_message, [account])
        return SendEmailOutput(send_result=json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        return SendEmailOutput(send_result=f"发送失败: {exc}")