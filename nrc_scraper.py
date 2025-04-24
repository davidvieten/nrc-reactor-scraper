import pandas as pd
import requests
from io import StringIO
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

print("✅ RUNNING NRC Scraper with Google Drive Upload")

# 1. Download NRC Data
url = "https://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/powerreactorstatusforlast365days.txt"
response = requests.get(url)
text_data = response.text

# 2. Parse Data
df = pd.read_csv(StringIO(text_data), sep="|")
df.columns = [col.strip() for col in df.columns]
df["ReportDt"] = pd.to_datetime(df["ReportDt"])
df["Power"] = pd.to_numeric(df["Power"], errors="coerce")
df["Status"] = df["Power"].apply(lambda x: "Online" if x > 0 else "Offline")

# 3. Save to Excel (temporary path for cloud)
filename = "reactor_status.xlsx"
df.to_excel(filename, index=False)
print(f"✅ Excel file created: {filename}")

# 4. Upload to Google Drive
def upload_excel_to_drive(file_path, file_name):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"✅ Uploaded to Google Drive. File ID: {uploaded_file.get('id')}")

# 5. Call uploader
upload_excel_to_drive(filename, filename)