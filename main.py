import requests
import random
import string
import os
from pymongo import MongoClient
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# Impostazioni MongoDB
MONGO_URI = "mongodb+srv://admin:Furkan10@miraculousitalia.cbpsh.mongodb.net/MiraculousItalia?retryWrites=true&w=majority"
DATABASE_NAME = "MiraculousItalia"
COLLECTION_NAME = "episodes"

# API Keys e URL
DROPLOAD_WORKER_BASE = "https://miraep.axelfireyt10.workers.dev/"
SUPERVIDEO_API_KEY = "22536ntvhqgnfbfdf6exk"
SUPERVIDEO_UPLOAD_URL = "https://supervideo.cc/api/upload/url"
SUPERVIDEO_SET_FOLDER_URL = "https://supervideo.cc/api/file/set_folder"

# Folder IDs su SuperVideo
FOLDER_IDS = {
    1: 28351,  # s1
    2: 28352,  # s2
    3: 28353,  # s3
    4: 28354,  # s4
    5: 28355   # s5
}

# Connessione a MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
episodes_collection = db[COLLECTION_NAME]

# Google Drive API Setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = "credentials.json"

def estrai_file_code(video_url):
    """ Estrae il file_code dall'URL di Dropload """
    return video_url.strip().split("/")[-1] if video_url else None

def genera_nome_file(season, episode):
    """ Genera un nome per il file nel formato IT{season}{episode}_random.mp4 """
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"IT{season}{str(episode).zfill(2)}_{random_str}.mp4"

def scarica_file(worker_url, file_name):
    """ Scarica il file dal Worker """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Referer": "https://miraculousitalia.it"
    }

    try:
        response = requests.get(worker_url, headers=headers, stream=True)

        if response.status_code != 200:
            print(f"❌ Errore nel download: {response.status_code}")
            return None

        temp_file_path = f"./{file_name}"
        with open(temp_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Download completato: {temp_file_path}")
        return temp_file_path

    except Exception as e:
        print(f"❌ Errore durante il download: {e}")
        return None

def upload_to_drive(file_path, file_name):
    """ Carica un file su Google Drive e restituisce il link pubblico """
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    file_metadata = {
        'name': file_name,
        'mimeType': 'video/mp4'
    }
    media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    file_id = file.get('id')

    # Rendi il file pubblico
    service.permissions().create(
        fileId=file_id,
        body={'role': 'reader', 'type': 'anyone'}
    ).execute()

    file_link = f"https://drive.google.com/uc?id={file_id}&export=download"
    print(f"✅ File caricato su Google Drive: {file_link}")
    return file_link

def upload_to_supervideo_from_drive(drive_url):
    """ Carica un video su SuperVideo partendo da un link Google Drive """
    params = {
        "key": SUPERVIDEO_API_KEY,
        "url": drive_url,
        "adult": "0"
    }

    response = requests.get(SUPERVIDEO_UPLOAD_URL, params=params)

    if response.ok:
        data = response.json()
        if data.get("status") == 200:
            print(f"✅ Upload completato su SuperVideo: {data['result']}")
            return data["result"]
        else:
            print("❌ Errore nell'upload:", data)
    else:
        print(f"❌ HTTP Error: {response.status_code}")
    return None

def sposta_file_nella_cartella(file_code, folder_id):
    """ Sposta il file nella cartella corretta su SuperVideo """
    params = {
        "key": SUPERVIDEO_API_KEY,
        "file_code": file_code,
        "fld_id": folder_id
    }
    try:
        response = requests.get(SUPERVIDEO_SET_FOLDER_URL, params=params)
        if response.ok:
            data = response.json()
            if data.get("status") == 200:
                print(f"✅ File {file_code} spostato nella cartella {folder_id}")
                return True
            else:
                print("Errore nel cambio cartella:", data)
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print("❌ Eccezione durante il cambio cartella:", e)
    return False

def processa_episodi():
    """ Scarica i file dal Worker, li carica su Google Drive e poi li invia a SuperVideo """
    for episodio in episodes_collection.find():
        video_url = episodio.get("videoUrl")
        season = episodio.get("season")
        episode = episodio.get("episodeNumber")

        if not video_url or season not in FOLDER_IDS:
            print(f"⚠️ Episodio {episodio.get('slug', episodio.get('title', 'Sconosciuto'))} non valido o senza cartella associata.")
            continue

        file_code = estrai_file_code(video_url)
        if not file_code:
            print(f"⚠️ Impossibile estrarre file code per {video_url}")
            continue

        worker_url = f"{DROPLOAD_WORKER_BASE}?file_code={file_code}"
        file_name = genera_nome_file(season, episode)
        print(f"📂 Processando {episodio.get('slug')} → {file_name}")
        print(f"🔗 URL Worker: {worker_url}")

        file_path = scarica_file(worker_url, file_name)
        if not file_path:
            print(f"❌ Download fallito per {episodio.get('slug')}")
            continue

        drive_url = upload_to_drive(file_path, file_name)
        if not drive_url:
            print(f"❌ Upload su Drive fallito per {episodio.get('slug')}")
            continue

        supervideo_file_code = upload_to_supervideo_from_drive(drive_url)
        if supervideo_file_code:
            folder_id = FOLDER_IDS[season]
            sposta_file_nella_cartella(supervideo_file_code, folder_id)

        # Rimuove il file locale dopo l'upload per risparmiare spazio
        os.remove(file_path)

if __name__ == "__main__":
    processa_episodi()
