import hashlib
import os
import smtplib
from email.header import Header
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

# --- 設定項目 ---
URL = "https://www.jikken-baito.com/"

# GitHub Secrets（環境変数）から情報を安全に取得
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")
TO_EMAIL = os.environ.get("TO_EMAIL")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
HASH_FILE = "last_hash.txt"


def get_site_hash(url):
    """サイトのメインコンテンツを取得し、テキストの変化を判定するためのハッシュ値を計算"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # HTML解析とスクリプト・スタイルの除去
    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["script", "style", "meta", "noscript"]):
        element.decompose()

    # テキスト部分のみを抽出し、余白をトリム
    text_content = soup.get_text()
    cleaned_text = "\n".join(
        [line.strip() for line in text_content.splitlines() if line.strip()]
    )

    # テキストの変化を判定するためのMD5ハッシュ値を作成
    return hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()


def send_email_notification(subject, body):
    """GmailのSMTPサーバー経由でメールを送信"""
    if not all([GMAIL_USER, GMAIL_PASS, TO_EMAIL]):
        print(
            "エラー: GMAIL_USER, GMAIL_PASS, TO_EMAIL の環境変数が設定されていません。"
        )
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()  # SSL/TLS暗号化
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)


def check_for_updates():
    current_hash = get_site_hash(URL)

    # 初回実行時：ハッシュ値を保存して終了（誤通知を防止）
    if not os.path.exists(HASH_FILE):
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
        print("初回のウェブサイト状態を保存しました。")
        return

    # 前回保存したハッシュ値を読み込み
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        previous_hash = f.read().strip()

    # ハッシュ値を比較して更新チェック
    if current_hash != previous_hash:
        print("【検知】ウェブサイトの更新が確認されました。メールを送信します。")

        # ハッシュファイルを新しい状態に更新
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)

        # 通知メール作成
        subject = "【更新通知】実験バイトのサイトが更新されました"
        body = (
            f"実験バイト（https://www.jikken-baito.com/）の表示内容に変更がありました。\n\n"
            f"最新情報を確認してください：\n{URL}"
        )
        send_email_notification(subject, body)
    else:
        print("更新はありません。")


if __name__ == "__main__":
    check_for_updates()
