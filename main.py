import requests
import os
import sys
import time
import magic
from pymongo import MongoClient
from tqdm import tqdm

# Configurazione MongoDB
MONGO_URI = "mongodb+srv://admin:Furkan10@miraculousitalia.cbpsh.mongodb.net/MiraculousItalia?retryWrites=true&w=majority"
DATABASE_NAME = "MiraculousItalia"
COLLECTION_NAME = "episodes"

# Configurazione API
DROPLOAD_WORKER_BASE = "https://miraep.axelfireyt10.workers.dev/"
SUPERVIDEO_API_KEY = "22536ntvhqgnfbfdf6exk"
# Endpoint alternativo per l'upload
SUPERUPLOAD_URL = "https://hfs305.serversicuro.cc/upload/01"
# API per spostare il file nella cartella su SuperVideo
SUPERVIDEO_SET_FOLDER_URL = "https://supervideo.cc/api/file/set_folder"
# Endpoint per ottenere la lista dei file (per recuperare il file code)
SUPERVIDEO_FILE_LIST_URL = "https://supervideo.cc/api/file/list"

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

def estrai_file_code(video_url):
    """Estrae il file_code dall'URL di Dropload."""
    return video_url.strip().split("/")[-1] if video_url else None

def genera_nome_file(season, episode):
    """Genera un nome per il file in base alla stagione e all'episodio."""
    return f"IT{season}{str(episode).zfill(2)}.mp4"

def scarica_file(worker_url, file_name):
    """Scarica il file tramite il Worker mostrando una barra di avanzamento."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        print(f"⬇️ Scaricando {file_name} da {worker_url}...")
        response = requests.get(worker_url, headers=headers, stream=True)
        if response.status_code != 200:
            print(f"❌ Errore nel download: {response.status_code}")
            return None

        total_size = int(response.headers.get('content-length', 0))
        file_path = os.path.join("./", file_name)
        chunk_size = 8192

        with open(file_path, "wb") as f, tqdm(
            total=total_size, unit='B', unit_scale=True, desc=file_name
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

        print(f"✅ Download completato: {file_path}")
        return file_path

    except Exception as e:
        print(f"❌ Eccezione nel download: {e}")
        return None

def validate_video(file_path):
    """Verifica approfondita del file video."""
    mime = magic.Magic(mime=True)
    detected_type = mime.from_file(file_path)
    if "video/mp4" not in detected_type:
        raise ValueError(f"Formato non supportato: {detected_type}")
    return True

def get_filecode_by_name(file_name):
    """Recupera il filecode cercando il file per nome tramite l'API di SuperVideo."""
    params = {
        "key": SUPERVIDEO_API_KEY,
        "title": file_name
    }
    try:
        response = requests.get(SUPERVIDEO_FILE_LIST_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            results = data.get("result", [])
            for item in results:
                # Confronta il nome esatto del file
                if item.get("name") == file_name:
                    return item.get("filecode")
    except Exception as e:
        print(f"❌ Errore durante il recupero del filecode: {e}")
    return None

def upload_to_supervideo(file_path, file_name):
    """Carica il file su SuperVideo utilizzando l'endpoint alternativo e recupera il filecode."""
    try:
        validate_video(file_path)
        with open(file_path, 'rb') as f:
            files = {
                'api_key': (None, SUPERVIDEO_API_KEY),
                'file': (
                    f.name, 
                    f, 
                    'video/mp4', 
                    {'Content-Disposition': f'form-data; name="file"; filename="{f.name}"'}
                )
            }
            response = requests.post(SUPERUPLOAD_URL, files=files)
            
            # Gestione dell'errore dal server
            if "st>" in response.text:
                parts = response.text.split("st>")
                if len(parts) > 1:
                    error = parts[1].split("</textarea")[0]
                    print(f"❌ Errore server: {error}")
                else:
                    print(f"❌ Errore server: {response.text}")
                return None
            
            print("✅ Upload completato con successo!")
            # Recupera il filecode cercando il file per nome
            filecode = get_filecode_by_name(file_name)
            if filecode:
                print(f"✅ Trovato filecode: {filecode}")
            else:
                print("❌ Impossibile recuperare il filecode dal file list.")
            return filecode
    except Exception as e:
        print(f"🔥 Errore critico: {str(e)}")
        return None

def sposta_file_nella_cartella(file_code, folder_id):
    """Sposta il file caricato nella cartella corretta su SuperVideo."""
    params = {"key": SUPERVIDEO_API_KEY, "file_code": file_code, "fld_id": folder_id}
    try:
        response = requests.get(SUPERVIDEO_SET_FOLDER_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 200:
                print(f"✅ File {file_code} spostato nella cartella {folder_id}")
                return True
            else:
                print(f"❌ Errore cambio cartella: {data}")
        else:
            print(f"❌ HTTP Error durante cambio cartella: {response.status_code}")
    except Exception as e:
        print(f"❌ Eccezione nel cambio cartella: {e}")
    return False

def processa_episodi():
    """Processa tutti gli episodi e li trasferisce da Dropload a SuperVideo."""
    for episodio in episodes_collection.find():
        video_url = episodio.get("videoUrl")
        season = episodio.get("season")
        episode = episodio.get("episodeNumber")

        if not video_url or season not in FOLDER_IDS:
            print(f"⚠️ Episodio {episodio.get('slug', episodio.get('title', 'Sconosciuto'))} non valido.")
            continue

        file_code = estrai_file_code(video_url)
        if not file_code:
            print(f"⚠️ Impossibile estrarre file code per {video_url}")
            continue

        worker_url = f"{DROPLOAD_WORKER_BASE}?file_code={file_code}"
        file_name = genera_nome_file(season, episode)

        print(f"📂 Processando {episodio.get('slug', episodio.get('title', 'Episodio'))} → {file_name}")
        print(f"🔗 URL Worker: {worker_url}")

        file_path = scarica_file(worker_url, file_name)
        if not file_path:
            print(f"❌ Download fallito per {episodio.get('slug', episodio.get('title'))}.")
            continue

        supervideo_file_code = upload_to_supervideo(file_path, file_name)
        if not supervideo_file_code:
            print(f"❌ Upload fallito per {episodio.get('slug', episodio.get('title'))}.")
            os.remove(file_path)
            continue

        folder_id = FOLDER_IDS[season]
        sposta_file_nella_cartella(supervideo_file_code, folder_id)
        os.remove(file_path)
        print(f"🗑️ File locale eliminato: {file_path}")
        time.sleep(5)

if __name__ == "__main__":
    processa_episodi()
    print("✅ Tutti gli episodi sono stati processati. Il processo verrà ora terminato.")
    sys.exit(0)
