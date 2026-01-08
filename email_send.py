import os
import asyncio
import time
import smtplib
import mimetypes
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from dotenv import load_dotenv, find_dotenv

# Third-party libraries
import gspread
from google.oauth2.service_account import Credentials
from imap_tools import MailBox

# 1. SETUP & ENVIRONMENT
load_dotenv(find_dotenv())


def get_env_var(var_name):
    val = os.getenv(var_name)
    if not val:
        raise ValueError(f"Missing environment variable: {var_name}")
    return val


# Load credentials
# Hostinger SMTP Settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # 465 = SSL
SMTP_USER = os.getenv("SMTP_USER") or os.getenv("IMAP_USER")
SMTP_PASS = os.getenv("SMTP_PASS") or os.getenv("IMAP_PASS")

if not SMTP_USER or not SMTP_PASS:
    raise ValueError("Missing SMTP credentials. Set SMTP_USER/SMTP_PASS or IMAP_USER/IMAP_PASS in .env")

# Hostinger IMAP (used only to save a copy to Sent)
IMAP_HOST = os.getenv("IMAP_HOST", "imap.hostinger.com")
IMAP_USER = os.getenv("IMAP_USER") or SMTP_USER
IMAP_PASS = os.getenv("IMAP_PASS") or SMTP_PASS

if not IMAP_USER or not IMAP_PASS:
    raise ValueError("Missing IMAP credentials. Set IMAP_USER/IMAP_PASS in .env")

SENT_FOLDER = os.getenv("SENT_FOLDER", "Sent")
SAVE_TO_SENT = os.getenv("SAVE_TO_SENT", "1").strip().lower() in {"1", "true", "yes", "y"}

if SAVE_TO_SENT:
    print(f"Will save a copy to IMAP folder: {SENT_FOLDER}")

# IMPORTANT: if EMAIL_SEND_DRY_RUN=1, nothing is sent and nothing is saved.

# Dry run (default enabled)
DRY_RUN = os.getenv("EMAIL_SEND_DRY_RUN", "1").strip().lower() in {"1", "true", "yes", "y"}

# Google Sheets
SHEET_NAME = get_env_var("GOOGLE_SHEET_NAME")
WORKSHEET_NAME = get_env_var("GOOGLE_WORKSHEET_NAME")
CREDENTIALS_FILE = "decisive-coda-477814-g9-19c85fd06150.json"

# Attachments (optional)
# Tip: on WSL, use a Linux path like /mnt/d/... (and quote it in .env if it has spaces)
ATTACHMENTS_DIR = os.getenv("ATTACHMENTS_DIR", os.path.join(os.getcwd(), "tumnail"))


def generate_fixed_email_content(row_data):
    """Generate fixed email content based on row data"""
    # Extract and clean data
    channel_name = row_data.get('name', 'YouTube Creator').replace('\n', '').replace('\r', '').strip()

    # Extract just the subscriber count without the word "subscribers"
    raw_subscriber = row_data.get('subscriber', '1000')
    import re
    subscriber_match = re.search(r'([\d.,]+[KMB]?)', raw_subscriber) if raw_subscriber else None
    if subscriber_match:
        subscriber_count = subscriber_match.group(1)
    else:
        subscriber_count = raw_subscriber or '1000'

    channel_niche = row_data.get('catagory', 'General').replace('\n', '').replace('\r', '').strip()

    # Fixed email body with proper formatting
    email_body = f"""Dear {channel_name},

My name is Syed Murtaza Hassam. With over six years in the YouTube, Instagram, and TikTok space and a background in video production I bring proven growth expertise. I have managed, edited videos, and designed assets for every kind of content. My priority is reliability: I guarantee on-time delivery, every single time. I have helped channels scale up to 4M+ subscribers, with one of my edits hitting 4.4M views on a single video.

I have been following your channel {channel_name} and am highly impressed with the quality of your content in the {channel_niche} space. Achieving {subscriber_count} subscribers is a strong foundation, and I am confident that my expertise can help you accelerate your scaling and maximise your channel's growth more efficiently.

What I deliver:
1. High-CTR Thumbnails.
2. Engaging Video Edits.
3. Complete YouTube management & SEO.

If you'd like, I can create a FREE sample Thumbnail or Video Edit for your next video — no commitments.

Please have a look at my Portfolio attached down below.
syedmurtazahassam.com

Best Regards,

Syed Murtaza Hassam"""

    subject = f"Collaboration Opportunity with {channel_name}"

    return subject, email_body


# 3. GOOGLE SHEETS FETCHING
def fetch_sheet_data():
    print("Fetching data from Google Sheet URL...")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_url(SHEET_NAME)
    sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    return sheet.get_all_records()


# 4. SMTP SEND

def _build_message(recipient_email, subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = recipient_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg["Reply-To"] = SMTP_USER
    msg.set_content(body)

    if os.path.exists(ATTACHMENTS_DIR):
        files = [
            f for f in os.listdir(ATTACHMENTS_DIR)
            if os.path.isfile(os.path.join(ATTACHMENTS_DIR, f))
        ]
        if not files:
            print(f"  Warning: No files found in attachments dir: {ATTACHMENTS_DIR}")

        for filename in files:
            filepath = os.path.join(ATTACHMENTS_DIR, filename)

            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type:
                maintype, subtype = mime_type.split("/", 1)
            else:
                maintype, subtype = "application", "octet-stream"

            with open(filepath, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=filename,
                )

            print(f"  Added attachment: {filename} ({maintype}/{subtype})")
    else:
        print(f"  Warning: Attachments directory not found: {ATTACHMENTS_DIR}")

    return msg


def _append_to_sent(msg):
    # Save a copy to Sent via IMAP so it appears in Hostinger webmail
    try:
        with MailBox(IMAP_HOST).login(IMAP_USER, IMAP_PASS) as mailbox:
            # Check if the folder exists, if not try common alternatives
            folders = [f.name for f in mailbox.folder.list()]

            # Find the correct sent folder
            actual_sent_folder = SENT_FOLDER
            if SENT_FOLDER not in folders:
                # Try common sent folder names
                for folder_name in ['Sent', 'Sent Items', 'INBOX.Sent', 'Sent Messages']:
                    if folder_name in folders:
                        actual_sent_folder = folder_name
                        break

            mailbox.folder.set(actual_sent_folder)
            mailbox.client.append(
                actual_sent_folder,
                r'(\Seen)',  # Use raw string for the flag
                None,
                msg.as_bytes(),
            )
        print(f"  Saved copy to {actual_sent_folder}")
    except Exception as e:
        print(f"  WARNING: Could not save to Sent via IMAP: {e}")
        print(f"  Available folders: {[f.name for f in MailBox(IMAP_HOST).login(IMAP_USER, IMAP_PASS).folder.list()][:10]}")


def send_email(recipient_email, subject, body):
    if not recipient_email:
        raise ValueError("Row is missing 'email' field")

    print(f"Sending email to {recipient_email} via SMTP ({SMTP_HOST}:{SMTP_PORT})...")

    msg = _build_message(recipient_email, subject, body)

    if DRY_RUN:
        print("  DRY RUN enabled (EMAIL_SEND_DRY_RUN=1) — not sending.")
        print("\n--- EMAIL PREVIEW (first 800 chars) ---")
        preview = msg.as_string()
        print(preview[:800] + ("..." if len(preview) > 800 else ""))
        print("--- END PREVIEW ---\n")
        return

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    print("  SENT")

    if SAVE_TO_SENT:
        _append_to_sent(msg)


# 5. MAIN ORCHESTRATION
async def main():
    try:
        rows = fetch_sheet_data()
        print(f"Found {len(rows)} rows to process.")

        # Process first 1000 rows as a batch (or all if less than 1000)
        batch_size = min(1000, len(rows))
        batch_rows = rows[:batch_size]

        print(f"Processing batch of {len(batch_rows)} rows...")

        for i, row in enumerate(batch_rows, 1):
            print(f"\nProcessing row {i}/{len(batch_rows)}: {row.get('name')}")

            # 1. Generate Fixed Content (no AI)
            try:
                subject, body = generate_fixed_email_content(row)
            except Exception as e:
                print(f"  Content generation failed: {e}")
                # Fallback to basic template
                name = row.get("name", "Creator")
                subject = f"Collaboration Opportunity with {name}"
                body = f"""Hi {name},

I hope this message finds you well! I've been following your YouTube channel '{row.get('channel')}' and love your content in the {row.get('catagory')} space.

I'd love to discuss a potential collaboration opportunity that could benefit both our audiences.

Best regards,
Team Automation"""

            # 2. Send Email
            send_email(row.get("email"), subject, body)

            # Wait 2 seconds to avoid rate limits
            time.sleep(2)

        print(f"\nBatch of {len(batch_rows)} emails processed successfully!")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())