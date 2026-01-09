import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import os
import csv
import io
from fastapi import UploadFile, File

# Import existing modules
# We need to be careful about relative imports or path issues if running from different cwd
# Assuming we run uvicorn from d:\Hamza coding\email-draft
try:
    import email_send
    import email_drafter
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Fallback for when running in a different context, though we expect to run in root
    import sys
    sys.path.append(os.getcwd())
    import email_send
    import email_drafter

app = FastAPI(title="Email Automation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RowData(BaseModel):
    row_index: int
    data: Dict[str, Any]

class BatchProcessRequest(BaseModel):
    rows: List[RowData]

class PreviewRequest(BaseModel):
    data: Dict[str, Any]

@app.get("/api/sheets")
async def get_sheet_data():
    try:
        # We can use either module's fetch function
        rows = email_send.fetch_sheet_data()
        # Add an index to each row to help with identification in UI
        indexed_rows = [{"row_index": i, "data": row} for i, row in enumerate(rows)]
        return {"count": len(rows), "rows": indexed_rows}
    except Exception as e:
        logger.error(f"Error fetching sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/preview")
async def preview_email(request: PreviewRequest):
    try:
        # Use email_send's generator as it seems to be the primary one for sending
        # Both files seem to have similar logic, but let's stick to email_send for now
        subject, body = email_send.generate_fixed_email_content(request.data)
        return {"subject": subject, "body": body}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        
        # Try different encodings
        text = None
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                text = contents.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if text is None:
            raise ValueError("Could not decode file with supported encodings (utf-8, latin-1)")
            
        csv_file = io.StringIO(text)
        
        # Check dialect (comma, semicolon, etc)
        # simplistic approach: let DictReader handle it or default to comma
        # We can also attempt to sniff
        try:
            sample = text[:1024]
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = 'excel' # default
            
        csv_file.seek(0)
        reader = csv.DictReader(csv_file, dialect=dialect)
        
        # Clean rows
        rows = []
        for row in reader:
            # Strip whitespace from keys and values if possible
            clean_row = {k.strip() if k else k: v.strip() if v else v for k, v in row.items() if k}
            if clean_row: # skip empty rows
                rows.append(clean_row)
        
        # Add index
        indexed_rows = [{"row_index": i, "data": row} for i, row in enumerate(rows)]
        return {"count": len(rows), "rows": indexed_rows}
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

@app.post("/api/send")
async def send_single_email(request: RowData):
    row = request.data
    email = row.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email address in row data")
    
    try:
        subject, body = email_send.generate_fixed_email_content(row)
        # We use standard synchronous send_email
        # Ideally this should be async or run in threadpool to not block
        # For simplicity in this local tool, direct call is okay if volume is low, 
        # but let's use to_thread for safety
        await asyncio.to_thread(email_send.send_email, email, subject, body)
        return {"status": "sent", "email": email}
    except Exception as e:
        logger.error(f"Error sending to {email}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/draft")
async def draft_single_email(request: RowData):
    row = request.data
    email = row.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email address in row data")
    
    try:
        # Note: email_drafter logic for content generation
        subject, body = email_drafter.generate_fixed_email_content(row)
        await asyncio.to_thread(email_drafter.save_to_drafts, email, subject, body)
        return {"status": "drafted", "email": email}
    except Exception as e:
        logger.error(f"Error drafting for {email}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch-send")
async def batch_send(request: BatchProcessRequest):
    results = []
    for item in request.rows:
        try:
            row = item.data
            email = row.get("email")
            if not email:
                results.append({"row_index": item.row_index, "status": "error", "error": "No email"})
                continue
            
            subject, body = email_send.generate_fixed_email_content(row)
            await asyncio.to_thread(email_send.send_email, email, subject, body)
            results.append({"row_index": item.row_index, "status": "success"})
            
            # Rate limiting delay
            await asyncio.sleep(2) 
        except Exception as e:
            results.append({"row_index": item.row_index, "status": "error", "error": str(e)})
            
    return {"results": results}

@app.post("/api/batch-draft")
async def batch_draft(request: BatchProcessRequest):
    results = []
    for item in request.rows:
        try:
            row = item.data
            email = row.get("email")
            if not email:
                results.append({"row_index": item.row_index, "status": "error", "error": "No email"})
                continue
            
            subject, body = email_drafter.generate_fixed_email_content(row)
            await asyncio.to_thread(email_drafter.save_to_drafts, email, subject, body)
            results.append({"row_index": item.row_index, "status": "success"})
            
            # Rate limiting delay
            await asyncio.sleep(2)
        except Exception as e:
            results.append({"row_index": item.row_index, "status": "error", "error": str(e)})
            
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    # Reload=True is good for dev
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
