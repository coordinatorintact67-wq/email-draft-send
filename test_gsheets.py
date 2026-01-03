import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv, find_dotenv

# Load .env
load_dotenv(find_dotenv())

def get_env_var(var_name):
    val = os.getenv(var_name)
    if not val:
        raise ValueError(f"Missing environment variable: {var_name}")
    return val

# Config
SHEET_NAME = get_env_var("GOOGLE_SHEET_NAME")
WORKSHEET_NAME = get_env_var("GOOGLE_WORKSHEET_NAME")
CREDENTIALS_FILE = "decisive-coda-477814-g9-19c85fd06150.json"

def test_fetch():
    print(f"Connecting to Google Sheets...")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    print(f"Opening Spreadsheet URL...")
    spreadsheet = client.open_by_url(SHEET_NAME)

    print(f"Opening Worksheet: {WORKSHEET_NAME}...")
    sheet = spreadsheet.worksheet(WORKSHEET_NAME)

    rows = sheet.get_all_records()
    print(f"\nSUCCESS! Found {len(rows)} rows.")

    if rows:
        print("\n--- ALL DATA ROWS ---")
        for i, row in enumerate(rows, 1):
            print(f"Row {i}: {row}")
        print("----------------------\n")
    else:
        print("Sheet is empty (besides headers).")

if __name__ == "__main__":
    try:
        test_fetch()
    except Exception as e:
        print(f"ERROR: {e}")
