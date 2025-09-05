import os
import json
import re
import glob
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import pdfplumber
from jsonschema import validate, ValidationError
import openai     # <-- NEW

# === OPENAI SETUP ===
openai.api_key = os.getenv("MY API KEY")
# Make sure to set this environment variable, e.g., in terminal: export OPENAI_API_KEY='your-api-key'

# === FOLDER SETUP ===
github_repo_path = os.path.expanduser('~/Documents/GitHub/get-init')
download_folder = os.path.join(github_repo_path, 'downloaded_files')
text_folder = os.path.join(github_repo_path, 'extracted_text')
json_folder = os.path.join(github_repo_path, 'json_output')

os.makedirs(download_folder, exist_ok=True)
os.makedirs(text_folder, exist_ok=True)
os.makedirs(json_folder, exist_ok=True)

# === JSON SCHEMA (for validation, now includes 'summary' as optional) ===
json_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "date": {"type": "string"},
        "body": {"type": "string"},
        "summary": {"type": "string"}      # <-- NEW
    },
    "required": ["title", "date", "body"]
}

# === HELPER: OPENAI SUMMARIZATION ===
def summarize_with_openai(text):
    if not openai.api_key:
        print("❌ No OpenAI API key found in environment variable OPENAI_API_KEY.")
        return ""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who summarizes documents."},
                {"role": "user", "content": f"Summarize the following document:\n\n{text}"}
            ],
            max_tokens=256,
            temperature=0.5,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"❌ OpenAI summarization failed: {e}")
        return ""

# === HELPER: PDF TO TXT + JSON ===
def extract_text_from_pdf(pdf_path, txt_path, json_path, title):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            for page in pdf.pages:
                all_text += page.extract_text() or ""

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(all_text)

        # Optionally, you could summarize here instead of Day 3.
        json_data = {
            "title": title,
            "content": all_text.strip()
        }
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(json_data, jf, indent=2)

        print(f"✅ Extracted: {title}")

    except Exception as e:
        print(f"❌ Failed to process {pdf_path}: {e}")

# === HELPER: FIND DATE IN TEXT ===
def find_date_in_text(text):
    match = re.search(r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b.*?\d{4}|\d{1,2}/\d{1,2}/\d{2,4})', text)
    return match.group(0) if match else "Not found"

# === BULK TXT ➝ JSON MAPPING ===
def bulk_convert_txt_to_json():
    print("\n🔁 Day 3: Converting TXT to structured JSON...")
    txt_files = glob.glob(os.path.join(text_folder, "*.txt"))
    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            title = lines[0].strip() if lines else ''
            body = ''.join(lines[1:]).strip()
            full_text = title + '\n' + body
            date = find_date_in_text(full_text)
            print(f"🤖 Summarizing {txt_file} with OpenAI...")
            # Limit body size for API; you can tune this limit
            body_for_summary = body if len(body) < 3000 else body[:3000]
            summary = summarize_with_openai(body_for_summary)

            data = {
                "title": title,
                "date": date,
                "body": body,
                "summary": summary
            }

        json_filename = os.path.basename(txt_file).replace('.txt', '.json')
        json_path = os.path.join(json_folder, json_filename)
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(data, jf, indent=2)

        print(f"✅ Converted {txt_file} → {json_path}")
    print("🎉 Day 3 complete.")

# === VALIDATION FUNCTION ===
def validate_json_outputs():
    print("\n🔍 Day 4: Validating JSON output files...")
    json_files = glob.glob(os.path.join(json_folder, "*.json"))
    invalid_files = []
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as jf:
            data = json.load(jf)
        try:
            validate(instance=data, schema=json_schema)
            print(f"✅ Valid: {json_file}")
        except ValidationError as e:
            print(f"❌ INVALID: {json_file} -- Reason: {e.message}")
            invalid_files.append(json_file)
    if not invalid_files:
        print("🎉 All JSON files are valid!")
    else:
        print(f"⚠️ {len(invalid_files)} invalid file(s) found.")

# === MAIN WORKFLOW ===
def main():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    folder_id = '1cuXVilrJSORTU-Jkm3x-qif2tu6FyiY-'  # Google Drive folder ID

    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    print("📄 Files in folder:")

    for file in file_list:
        print(f'{file["title"]} ({file["id"]}) - {file["mimeType"]}')

    for file in file_list:
        title = file['title']
        mime = file['mimeType']
        base_title = title.replace('.pdf', '').strip()

        pdf_filename = f"{base_title}.pdf"
        txt_filename = f"{base_title}.txt"
        json_filename = f"{base_title}.json"

        pdf_path = os.path.join(download_folder, pdf_filename)
        txt_path = os.path.join(text_folder, txt_filename)
        json_path = os.path.join(json_folder, json_filename)

        # Case 1: Google Doc
        if mime == 'application/vnd.google-apps.document':
            print(f"📤 Exporting Google Doc '{title}' as PDF...")
            file.GetContentFile(pdf_path, mimetype='application/pdf')

        # Case 2: Native PDF
        elif title.lower().endswith('.pdf'):
            print(f"⬇️ Downloading PDF '{title}'...")
            file.GetContentFile(pdf_path)

        else:
            print(f"⏩ Skipping unsupported file: {title} ({mime})")
            continue

        print(f"📝 Extracting text and saving JSON for '{title}'...")
        extract_text_from_pdf(pdf_path, txt_path, json_path, base_title)

    # === Bulk Convert Existing TXT Files to JSON & summarize ===
    bulk_convert_txt_to_json()

    # === Day 4: Validate all JSON outputs ===
    validate_json_outputs()

    print("\n✅ All files saved.")
    print("📂 Texts:", text_folder)
    print("📂 JSONs:", json_folder)

if __name__ == "__main__":
    main()


