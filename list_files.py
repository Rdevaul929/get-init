from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
import os
# If modifying scopes, delete token.json first
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Folder ID from your URL
FOLDER_ID = '1cuXVilrJSORTU-Jkm3x-qif2tu6FyiY-'

def download_file(service, file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    filepath = os.path.join(os.getcwd(), file_name)
    with open(filepath, 'wb') as f:
        downloader = request.Request()
        response = service._http.request(request.uri)
        f.write(response[1])
    print(f"Downloaded: {file_name}")
    
def main():
    # Authenticate
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json', SCOPES)
    creds = flow.run_local_server(port=8080)

    # Build service
    service = build('drive', 'v3', credentials=creds)

    # Print authenticated email
    user_info = service.about().get(fields='user').execute()
    print("Authenticated as:", user_info['user']['emailAddress'])

    # Query files in folder
    query = f"'{FOLDER_ID}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print("No files found.")
    else:
        print("Files in folder:")
        for item in items:
            print(f"{item['name']} ({item['id']})")

if __name__ == '__main__':
    main()

git init
git add .
git commit -m "initial commit: download PDFs from Drive"

