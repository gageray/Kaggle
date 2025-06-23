from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    return creds

def upload_file(service, filepath, parent_folder_id=None):
    file_metadata = {'name': os.path.basename(filepath)}
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]

    media = MediaFileUpload(filepath, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"Uploaded {filepath} -> File ID: {file['id']}")

if __name__ == '__main__':
    service = build('drive', 'v3', credentials=authenticate())
    
    # Upload files from out directory
    if os.path.exists('out'):
        for filename in os.listdir('out'):
            filepath = os.path.join('out', filename)
            if os.path.isfile(filepath):
                upload_file(service, filepath)
    else:
        print("No 'out' directory found. Nothing to upload.")