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
from agents import Agent, RunConfig, AsyncOpenAI, OpenAIChatCompletionsModel, Runner

# 1. SETUP & ENVIRONMENT
load_dotenv(find_dotenv())


def get_env_var(var_name):
    val = os.getenv(var_name)
    if not val:
        raise ValueError(f"Missing environment variable: {var_name}")
    return val


# Load credentials
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = get_env_var("GEMINI_API_KEY")

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



# 2. AI AGENT CONFIGURATION (OpenRouter)
if OPENROUTER_API_KEY:
    provider = AsyncOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    model = OpenAIChatCompletionsModel(
        model="openai/gpt-4o-mini",
        openai_client=provider,
    )
    print("Using OpenRouter API (openai/gpt-4o-mini)")
else:
    raise ValueError("OPENROUTER_API_KEY not found. Please add it to .env file")

run_config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True,
)

agent = Agent(
    instructions="""You are a professional email writer.
    Write a highly personalized, concise outreach email.
    Use the provided channel name and category to make it relevant.
    Do not use placeholders like [Your Name], sign off as 'Team Automation'.""",
    name="Email Sender Agent",
)


async def generate_email_body(row_data):
    """row_data: dict with name, email, channel, subscriber, catagory"""
    prompt = f"""
    Write an email to {row_data['name']} who runs the YouTube channel '{row_data['channel']}'.
    The channel is in the '{row_data['catagory']}' category and has {row_data['subscriber']} subscribers.
    Subject line should be catchy.
    Format:
    Subject: [Catchy Subject]
    ---
    [Email Body]
    """

    result = await Runner.run(
        agent,
        input=prompt,
        run_config=run_config,
    )
    return result.final_output


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
            mailbox.folder.set(SENT_FOLDER)
            mailbox.client.append(
                SENT_FOLDER,
                "(\\Seen)",
                None,
                msg.as_bytes(),
            )
        print(f"  Saved copy to {SENT_FOLDER}")
    except Exception as e:
        print(f"  WARNING: Could not save to Sent via IMAP: {e}")


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

        for i, row in enumerate(rows, 1):
            print(f"\nProcessing row {i}/{len(rows)}: {row.get('channel')}")

            # 1. Generate Content
            try:
                ai_output = await generate_email_body(row)

                if "---" in ai_output:
                    subject_part, body_part = ai_output.split("---", 1)
                    subject = subject_part.replace("Subject:", "").strip()
                    body = body_part.strip()
                else:
                    subject = f"Collaboration with {row.get('channel', '')}".strip() or "Collaboration"
                    body = ai_output

            except Exception as e:
                print(f"  AI generation failed, using template: {e}")
                name = row.get("name", "Creator")
                subject = f"Collaboration Opportunity with {name}"
                body = f"""Hi {name},

I hope this message finds you well! I've been following your YouTube channel '{row.get('channel')}' and love your content in the {row.get('catagory')} space.

I'd love to discuss a potential collaboration opportunity that could benefit both our audiences.

Best regards,\nTeam Automation"""

            # 2. Send Email
            send_email(row.get("email"), subject, body)

            # Wait 2 seconds to avoid rate limits
            time.sleep(2)

        print("\nAll emails processed successfully!")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
