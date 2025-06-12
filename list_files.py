from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
if not os.path.exists('downloads'):
    os.makedirs('downloads')
def main():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Opens a browser to authenticate
    drive = GoogleDrive(gauth)

    folder_id = '1cuXVilrJSORTU-Jkm3x-qif2tu6FyiY-'  # Replace this!

    # List files in the folder
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    print("Files in folder:")
    for file in file_list:
        print(f'{file["title"]} ({file["id"]})')

    # Download PDF files
    for file in file_list:
        if file['title'].lower().endswith('.pdf'):
            print(f"Downloading {file['title']}...")
            file.GetContentFile(f"downloads/{file['title']}")

    # Check your local directory for downloaded files
    print("\nFiles in current directory:")
    print(os.listdir())

if __name__ == "__main__":
    main()
