import os
from email.message import EmailMessage
from dotenv import load_dotenv, find_dotenv
from imap_tools import MailBox

# 1. SETUP
load_dotenv(find_dotenv())

IMAP_HOST = "imap.hostinger.com"
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")

def test_imap_draft():
    print(f"Connecting to Hostinger IMAP: {IMAP_HOST}...")

    # Sample data for testing
    recipient = "ahmedilyas@intactonesolution.com"
    subject = "TEST DRAFT: Collaboration with Proper DIY (WITH ATTACHMENT)"
    body = "Hi Proper DIY,\n\nThis is a test draft saved via automation script with attachments.\n\nPlease see the attached images.\n\nRegards,\nTeam Automation"

    # Construct the email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = IMAP_USER
    msg['To'] = recipient
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
