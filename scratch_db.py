import sys
import os
sys.path.insert(0, r'c:\Users\arulj\Documents\Projects\SmartBI\backend')
from app.services.database_service import DatabaseService  # type: ignore
import json
from dotenv import load_dotenv

load_dotenv()

db = DatabaseService(os.getenv('SMARTBI_DATABASE_URL'))
uploads = db.fetch_all("SELECT id, file_name, domain_name, confidence FROM smartbi_uploads ORDER BY created_at DESC LIMIT 5")

for u in uploads:
    print(f"File: {u['file_name']} Domain: {u['domain_name']} Confidence: {u['confidence']}")
    _, rows = db.fetch_upload_dataset(u['id'])
    if rows:
        print(f"Columns: {list(rows[0].keys())}")
        print(f"First row: {rows[0]}")
    print("-" * 40)
