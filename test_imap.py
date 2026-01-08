import os
from email.message import EmailMessage
from dotenv import load_dotenv, find_dotenv
from imap_tools import MailBox

# Third-party libraries for Google Sheets
import gspread
from google.oauth2.service_account import Credentials

# 1. SETUP
load_dotenv(find_dotenv())

def get_env_var(var_name):
    val = os.getenv(var_name)
    if not val:
        raise ValueError(f"Missing environment variable: {var_name}")
    return val

IMAP_HOST = "imap.hostinger.com"
IMAP_USER = get_env_var("IMAP_USER")
IMAP_PASS = get_env_var("IMAP_PASS")
SHEET_NAME = get_env_var("GOOGLE_SHEET_NAME")
WORKSHEET_NAME = get_env_var("GOOGLE_WORKSHEET_NAME")
CREDENTIALS_FILE = "decisive-coda-477814-g9-19c85fd06150.json"  # Path to your Google Service Account JSON

def fetch_sheet_data():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_url(SHEET_NAME)
    sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    return sheet.get_all_records()

def test_imap_draft():
    print(f"Connecting to Hostinger IMAP: {IMAP_HOST}...")

    # Fetch data from Google Sheets
    try:
        rows = fetch_sheet_data()
        print(f"Found {len(rows)} rows to process.")

        if len(rows) > 0:
            # Process first 10 rows as a batch (or all if less than 10)
            batch_size = min(10, len(rows))
            batch_rows = rows[:batch_size]

            print(f"Processing batch of {len(batch_rows)} rows...")

            for idx, row in enumerate(batch_rows):
                print(f"\nProcessing row {idx + 1}:")

                # Extract data from the row
                recipient = row.get('email', '')  # Don't use default, check if empty later
                channel_name = row.get('name', '')  # Don't use default, check if empty later
                # Clean the channel name by removing any line feeds or carriage returns
                channel_name = channel_name.replace('\n', '').replace('\r', '').strip() if channel_name else 'Default Channel'

                raw_channel = row.get('channel', 'https://www.youtube.com/@RaviTeluguVlogs')  # Keep URL for reference

                # Extract just the subscriber count without the word "subscribers"
                raw_subscriber = row.get('subscriber', '')
                # Remove "subscribers" and any extra text, keeping just the number
                import re
                subscriber_match = re.search(r'([\d.,]+[KMB]?)', raw_subscriber) if raw_subscriber else None
                if subscriber_match:
                    subscriber_count = subscriber_match.group(1)
                else:
                    subscriber_count = raw_subscriber or '1000'  # fallback if no match

                channel_niche = row.get('catagory', '')  # Don't use default, check if empty later
                # Clean the channel niche by removing any line feeds or carriage returns
                channel_niche = channel_niche.replace('\n', '').replace('\r', '').strip() if channel_niche else 'General'

                # Validate that we have required fields
                if not recipient or not channel_name:
                    print(f"  Skipping row {idx + 1}: Missing required fields (email: {recipient}, name: {channel_name})")
                    continue  # Skip this row and continue with the next

                subject = f"TEST DRAFT: Collaboration with {channel_name} (WITH ATTACHMENT)"

                print(f"  Channel: {channel_name}, Subscribers: {subscriber_count}, Niche: {channel_niche}")

                # Email structure according to the specified prompt with dynamic data
                # Using HTML format to support proper bold and italic formatting
                html_body = f"""<!DOCTYPE html>
<html>
<head></head>
<body>
<p><strong>Dear {channel_name}</strong>,</p>

<p>My name is <strong>Syed Murtaza Hassam</strong>. With over <strong>six years</strong> in the YouTube, Instagram, and TikTok space and a background in video production I bring proven growth expertise. I have managed, edited videos, and designed assets for every kind of content. My priority is reliability: I <strong>guarantee on-time delivery, every single time</strong>. I have helped channels scale up to <strong>4M+ subscribers</strong>, with one of my edits hitting <strong>4.4M views</strong> on a single video.</p>

<p>I have been following your channel <strong>{channel_name}</strong> and am highly impressed with the quality of your content in the <strong><em>{channel_niche}</em></strong> space. Achieving <strong>{subscriber_count} subscribers</strong> is a strong foundation, and I am confident that my expertise can help you accelerate your scaling and maximise your channel's growth more efficiently.</p>

<p><strong>What I deliver:</strong><br>
<ol>
<li>High-CTR Thumbnails.</li>
<li>Engaging Video Edits.</li>
<li>Complete YouTube management & SEO.</li>
</ol></p>

<p>If you'd like, I can create a FREE sample Thumbnail or Video Edit for your next video — no commitments.</p>

<p>Please have a look at my Portfolio attached down below.<br>
<a href="https://syedmurtazahassam.com">syedmurtazahassam.com</a></p>

<p>Best Regards,</p>

<p><strong>Syed Murtaza Hassam</strong></p>
</body>
</html>"""

                # Plain text fallback
                text_body = f"""Dear {channel_name},

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

                # Construct the email message
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = IMAP_USER
                msg['To'] = recipient

                # Set both plain text and HTML content
                msg.set_content(text_body)
                msg.add_alternative(html_body, subtype='html')

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
                else:
                    print(f"  Warning: Attachments directory not found: {attachments_dir}")

                try:
                    with MailBox(IMAP_HOST).login(IMAP_USER, IMAP_PASS) as mailbox:
                        # List folders to find Drafts
                        folders = [f.name for f in mailbox.folder.list()]

                        # Try to determine the Drafts folder name
                        target_folder = 'Drafts'
                        if 'Drafts' not in folders:
                            if 'INBOX.Drafts' in folders:
                                target_folder = 'INBOX.Drafts'
                            elif 'INBOX/Drafts' in folders:
                                target_folder = 'INBOX/Drafts'

                        # Append the message
                        mailbox.folder.set(target_folder)
                        mailbox.client.append(
                            target_folder,
                            '(\\Draft)',
                            None,
                            msg.as_bytes()
                        )
                        print(f"  SUCCESS! Draft saved for {channel_name} ({recipient}) to {target_folder}.")

                except Exception as e:
                    print(f"  IMAP ERROR for {channel_name}: {e}")

        else:
            # Fallback values if no data in sheet
            recipient = "ahmedilyas@intactonesolution.com"
            channel_name = "Ravi Telugu Vlogs"
            subscriber_count = "3.62K"
            channel_niche = "Daily Vlogs"
            subject = "TEST DRAFT: Collaboration with Proper DIY (WITH ATTACHMENT)"

            print(f"Using fallback data - Channel: {channel_name}, Subscribers: {subscriber_count}, Niche: {channel_niche}")

            # Email structure according to the specified prompt
            # Using HTML format to support proper bold and italic formatting
            html_body = f"""<!DOCTYPE html>
<html>
<head></head>
<body>
<p><strong>Dear {channel_name}</strong>,</p>

<p>My name is <strong>Syed Murtaza Hassam</strong>. With over <strong>six years</strong> in the YouTube, Instagram, and TikTok space and a background in video production I bring proven growth expertise. I have managed, edited videos, and designed assets for every kind of content. My priority is reliability: I <strong>guarantee on-time delivery, every single time</strong>. I have helped channels scale up to <strong>4M+ subscribers</strong>, with one of my edits hitting <strong>4.4M views</strong> on a single video.</p>

<p>I have been following your channel <strong>{channel_name}</strong> and am highly impressed with the quality of your content in the <strong><em>{channel_niche}</em></strong> space. Achieving <strong>{subscriber_count} subscribers</strong> is a strong foundation, and I am confident that my expertise can help you accelerate your scaling and maximise your channel's growth more efficiently.</p>

<p><strong>What I deliver:</strong><br>
<ol>
<li>High-CTR Thumbnails.</li>
<li>Engaging Video Edits.</li>
<li>Complete YouTube management & SEO.</li>
</ol></p>

<p>If you'd like, I can create a FREE sample Thumbnail or Video Edit for your next video — no commitments.</p>

<p>Please have a look at my Portfolio attached down below.<br>
<a href="https://syedmurtazahassam.com">syedmurtazahassam.com</a></p>

<p>Best Regards,</p>

<p><strong>Syed Murtaza Hassam</strong></p>
</body>
</html>"""

            # Plain text fallback
            text_body = f"""Dear {channel_name},

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

            # Construct the email message
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = IMAP_USER
            msg['To'] = recipient

            # Set both plain text and HTML content
            msg.set_content(text_body)
            msg.add_alternative(html_body, subtype='html')

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
                        print(f"Added attachment: {filename}")
            else:
                print(f"Warning: Attachments directory not found: {attachments_dir}")

            try:
                with MailBox(IMAP_HOST).login(IMAP_USER, IMAP_PASS) as mailbox:
                    # List folders to find Drafts
                    print("Checking available folders...")
                    folders = [f.name for f in mailbox.folder.list()]
                    print(f"Folders found: {folders}")

                    # Try to determine the Drafts folder name
                    target_folder = 'Drafts'
                    if 'Drafts' not in folders:
                        if 'INBOX.Drafts' in folders:
                            target_folder = 'INBOX.Drafts'
                        elif 'INBOX/Drafts' in folders:
                            target_folder = 'INBOX/Drafts'

                    print(f"Targeting folder: {target_folder}")

                    # Append the message
                    mailbox.folder.set(target_folder)
                    mailbox.client.append(
                        target_folder,
                        '(\\Draft)',
                        None,
                        msg.as_bytes()
                    )
                    print("\nSUCCESS! Test draft saved successfully to Hostinger.")

            except Exception as e:
                print(f"\nIMAP ERROR: {e}")

    except Exception as e:
        print(f"Error fetching data from Google Sheets: {e}")
        # Fallback to original values
        recipient = "ahmedilyas@intactonesolution.com"
        channel_name = "Ravi Telugu Vlogs"
        subscriber_count = "3.62K"
        channel_niche = "Daily Vlogs"
        subject = "TEST DRAFT: Collaboration with Proper DIY (WITH ATTACHMENT)"

        # Email structure according to the specified prompt
        # Using HTML format to support proper bold and italic formatting
        html_body = f"""<!DOCTYPE html>
<html>
<head></head>
<body>
<p><strong>Dear {channel_name}</strong>,</p>

<p>My name is <strong>Syed Murtaza Hassam</strong>. With over <strong>six years</strong> in the YouTube, Instagram, and TikTok space and a background in video production I bring proven growth expertise. I have managed, edited videos, and designed assets for every kind of content. My priority is reliability: I <strong>guarantee on-time delivery, every single time</strong>. I have helped channels scale up to <strong>4M+ subscribers</strong>, with one of my edits hitting <strong>4.4M views</strong> on a single video.</p>

<p>I have been following your channel <strong>{channel_name}</strong> and am highly impressed with the quality of your content in the <strong><em>{channel_niche}</em></strong> space. Achieving <strong>{subscriber_count} subscribers</strong> is a strong foundation, and I am confident that my expertise can help you accelerate your scaling and maximise your channel's growth more efficiently.</p>

<p><strong>What I deliver:</strong><br>
<ol>
<li>High-CTR Thumbnails.</li>
<li>Engaging Video Edits.</li>
<li>Complete YouTube management & SEO.</li>
</ol></p>

<p>If you'd like, I can create a FREE sample Thumbnail or Video Edit for your next video — no commitments.</p>

<p>Please have a look at my Portfolio attached down below.<br>
<a href="https://syedmurtazahassam.com">syedmurtazahassam.com</a></p>

<p>Best Regards,</p>

<p><strong>Syed Murtaza Hassam</strong></p>
</body>
</html>"""

        # Plain text fallback
        text_body = f"""Dear {channel_name},

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

        # Construct the email message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = IMAP_USER
        msg['To'] = recipient

        # Set both plain text and HTML content
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype='html')

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
                    print(f"Added attachment: {filename}")
        else:
            print(f"Warning: Attachments directory not found: {attachments_dir}")

        try:
            with MailBox(IMAP_HOST).login(IMAP_USER, IMAP_PASS) as mailbox:
                # List folders to find Drafts
                print("Checking available folders...")
                folders = [f.name for f in mailbox.folder.list()]
                print(f"Folders found: {folders}")

                # Try to determine the Drafts folder name
                target_folder = 'Drafts'
                if 'Drafts' not in folders:
                    if 'INBOX.Drafts' in folders:
                        target_folder = 'INBOX.Drafts'
                    elif 'INBOX/Drafts' in folders:
                        target_folder = 'INBOX/Drafts'

                print(f"Targeting folder: {target_folder}")

                # Append the message
                mailbox.folder.set(target_folder)
                mailbox.client.append(
                    target_folder,
                    '(\\Draft)',
                    None,
                    msg.as_bytes()
                )
                print("\nSUCCESS! Test draft saved successfully to Hostinger.")

        except Exception as e:
            print(f"\nIMAP ERROR: {e}")

if __name__ == "__main__":
    test_imap_draft()