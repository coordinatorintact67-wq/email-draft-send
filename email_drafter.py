import os
import asyncio
import time
import smtplib
from email.message import EmailMessage
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
IMAP_HOST = "imap.hostinger.com"
IMAP_USER = get_env_var("IMAP_USER")
IMAP_PASS = get_env_var("IMAP_PASS")
SHEET_NAME = get_env_var("GOOGLE_SHEET_NAME")
WORKSHEET_NAME = get_env_var("GOOGLE_WORKSHEET_NAME")
CREDENTIALS_FILE = "decisive-coda-477814-g9-19c85fd06150.json"  # Path to your Google Service Account JSON


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
    print(f"Fetching data from Google Sheet URL...")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_url(SHEET_NAME)
    sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    return sheet.get_all_records()

# 4. IMAP DRAFT CREATION
def save_to_drafts(recipient_email, subject, body):
    print(f"Saving draft for {recipient_email} to Hostinger...")

    # Construct the email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = IMAP_USER
    msg['To'] = recipient_email
    msg.set_content(body)

    # Add all attachments
    attachments_dir = "D:\\Coding\\email draft\\attachments"

    if os.path.exists(attachments_dir):
        for filename in os.listdir(attachments_dir):
            filepath = os.path.join(attachments_dir, filename)
            if os.path.isfile(filepath):
                with open(filepath, 'rb') as f:
                    ext = os.path.splitext(filename)[1][1:]
                    msg.add_attachment(
                        f.read(),
                        maintype='image',
                        subtype=ext,
                        filename=filename
                    )
                print(f"  Added attachment: {filename}")

    # Use imap-tools to append to Drafts
    with MailBox(IMAP_HOST).login(IMAP_USER, IMAP_PASS) as mailbox:
        # Hostinger usually uses 'Drafts' or 'INBOX.Drafts'
        # We'll try to find the folder if it's not standard
        target_folder = 'Drafts'
        folders = [f.name for f in mailbox.folder.list()]
        if 'Drafts' not in folders and 'INBOX.Drafts' in folders:
            target_folder = 'INBOX.Drafts'

        # Append message as a fast byte string
        mailbox.folder.set(target_folder)
        mailbox.client.append(
            target_folder,
            '(\\Draft)',
            None,
            msg.as_bytes()
        )
    print(f"Successfully saved to {target_folder}.")

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
            print(f"\nProcessing row {i}/{len(batch_rows)}: {row.get('channel')}")

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

            # 2. Save Draft
            save_to_drafts(row['email'], subject, body)

            # Wait 2 seconds to avoid rate limits
            time.sleep(2)

        print("\nAll drafts processed successfully!")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())