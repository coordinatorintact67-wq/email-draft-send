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
IMAP_HOST = "imap.hostinger.com"
IMAP_USER = get_env_var("IMAP_USER")
IMAP_PASS = get_env_var("IMAP_PASS")
SHEET_NAME = get_env_var("GOOGLE_SHEET_NAME")
WORKSHEET_NAME = get_env_var("GOOGLE_WORKSHEET_NAME")
CREDENTIALS_FILE = "decisive-coda-477814-g9-19c85fd06150.json"  # Path to your Google Service Account JSON

# 2. AI AGENT CONFIGURATION (OpenRouter)

# Use OpenRouter API
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
    name="Email Drafter Agent",
)

async def generate_email_body(row_data):
    """
    row_data: dictionary with name, email, channel, subscriber, catagory
    """
    prompt = f"""
    Write an email to {row_data['name']} who runs the YouTube channel '{row_data['channel']}'.
    The channel is in the '{row_data['catagory']}' category and has {row_data['subscriber']} subscribers.
    Subject line should be catchy.
    Format:
    Subject: [Catchy Subject]
    ---
    [Email Body]
    """

    # Use OpenRouter API
    result = await Runner.run(
        agent,
        input=prompt,
        run_config=run_config,
    )
    return result.final_output

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

        for i, row in enumerate(rows, 1):
            print(f"\nProcessing row {i}/{len(rows)}: {row['channel']}")

            # 1. Generate Content
            try:
                ai_output = await generate_email_body(row)

                # Split Subject and Body
                if "---" in ai_output:
                    subject_part, body_part = ai_output.split("---", 1)
                    subject = subject_part.replace("Subject:", "").strip()
                    body = body_part.strip()
                else:
                    subject = f"Collaboration with {row['channel']}"
                    body = ai_output
            except Exception as e:
                print(f"  AI generation failed, using template: {e}")
                # Fallback to template
                name = row.get('name', 'Creator')
                subject = f"Collaboration Opportunity with {name}"
                body = f"""Hi {name},

I hope this message finds you well! I've been following your YouTube channel '{row['channel']}' and love your content in the {row['catagory']} space. With {row['subscriber']} subscribers, your influence is impressive.

I'd love to discuss a potential collaboration opportunity that could benefit both our audiences.

Would you be open to a quick chat to explore how we might work together?

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
