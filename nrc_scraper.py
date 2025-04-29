import pandas as pd
import requests
from io import StringIO
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

print("✅ RUNNING NRC Scraper with Prepend + Google Drive Update")

# 1. Download NRC Data
url = "https://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/powerreactorstatusforlast365days.txt"
response = requests.get(url)
text_data = response.text

# 2. Parse Data
new_df = pd.read_csv(StringIO(text_data), sep="|")
new_df.columns = [col.strip() for col in new_df.columns]
new_df["ReportDt"] = pd.to_datetime(new_df["ReportDt"])
new_df["Power"] = pd.to_numeric(new_df["Power"], errors="coerce")
new_df["Status"] = new_df["Power"].apply(lambda x: "Online" if x > 0 else "Offline")

# 3. Combine with existing Excel (if it exists)
filename = "reactor_status.xlsx"

if os.path.exists(filename):
    old_df = pd.read_excel(filename)
    combined_df = pd.concat([new_df, old_df], ignore_index=True)
    combined_df.drop_duplicates(subset=["ReportDt", "Unit"], keep="first", inplace=True)
else:
    combined_df = new_df

# 4. Save updated Excel file
combined_df.to_excel(filename, index=False)
print(f"✅ Excel file updated locally: {filename}")

# 5. Upload to Google Drive (overwrite contents, keep file ID)
def upload_excel_to_drive(file_path, file_name):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('drive', 'v3', credentials=creds)

    # Check for existing file in Google Drive
    query = f"name='{file_name}' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])

    media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    if files:
        # File exists — update it
        file_id = files[0]['id']
        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"🔁 Updated existing file in Drive (ID: {file_id})")
    else:
        # File doesn't exist — create it
        file_metadata = {'name': file_name}
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"✅ Uploaded new file to Drive. File ID: {uploaded_file.get('id')}")

# 6. Run uploader
upload_excel_to_drive(filename, filename)