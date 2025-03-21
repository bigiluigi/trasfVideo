import requests
import random
import string
from pymongo import MongoClient

# Impostazioni MongoDB
MONGO_URI = "mongodb+srv://admin:Furkan10@miraculousitalia.cbpsh.mongodb.net/MiraculousItalia?retryWrites=true&w=majority"
DATABASE_NAME = "MiraculousItalia"
COLLECTION_NAME = "episodes"  # Nome della collection con gli episodi

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

def estrai_file_code(video_url):
    """
    Estrae il file_code dall'URL di Dropload, es: da https://dropload.io/0n763ple7cdt -> "0n763ple7cdt"
    """
    return video_url.strip().split("/")[-1] if video_url else None

def genera_nome_file(season, episode):
    """
    Genera un nome per il file nel formato IT{season}{episode}_random.mp4
    """
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"IT{season}{str(episode).zfill(2)}_{random_str}.mp4"

def upload_to_supervideo(worker_url, file_name):
    """
    Scarica il file dal Worker e lo carica su SuperVideo.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Referer": "https://miraculousitalia.it"
    }

    try:
        # Scarica il file dal Worker
        print(f"⬇️ Scaricando {file_name} da {worker_url}...")
        response = requests.get(worker_url, headers=headers, stream=True)

        if response.status_code != 200:
            print(f"❌ Errore nel download: {response.status_code}")
            return None

        # Salva il file temporaneamente
        temp_file_path = f"./{file_name}"
        with open(temp_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Download completato: {temp_file_path}")

        # Ora carichiamo il file su SuperVideo
        with open(temp_file_path, "rb") as f:
            files = {"file": (file_name, f)}
            params = {"key": SUPERVIDEO_API_KEY}
            upload_response = requests.post("https://supervideo.cc/api/upload", files=files, data=params)

        if upload_response.ok:
            data = upload_response.json()
            if data.get("status") == 200:
                return data.get("result", {}).get("filecode")
            else:
                print("Errore nell'upload:", data)
        else:
            print("HTTP Error:", upload_response.status_code)

    except Exception as e:
        print("❌ Eccezione durante l'upload:", e)

    return None

def sposta_file_nella_cartella(file_code, folder_id):
    """
    Sposta il file appena caricato nella cartella corretta su SuperVideo.
    """
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
            print("HTTP Error:", response.status_code)
    except Exception as e:
        print("Eccezione durante il cambio cartella:", e)
    return False

def processa_episodi():
    """
    Itera sugli episodi e li trasferisce da Dropload a SuperVideo.
    """
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

        # Costruisce l'URL del worker
        worker_url = f"{DROPLOAD_WORKER_BASE}?file_code={file_code}"

        # Genera il nome del file
        file_name = genera_nome_file(season, episode)
        print(f"📂 Processando {episodio.get('slug')} → {file_name}")
        print(f"🔗 URL Worker: {worker_url}")

        # Effettua l'upload su SuperVideo
        supervideo_file_code = upload_to_supervideo(worker_url, file_name)
        if supervideo_file_code:
            print(f"✅ Upload completato per {episodio.get('slug')} → {supervideo_file_code}")

            # Sposta il file nella cartella giusta
            folder_id = FOLDER_IDS[season]
            sposta_file_nella_cartella(supervideo_file_code, folder_id)
        else:
            print(f"❌ Upload fallito per {episodio.get('slug')}.")

if __name__ == "__main__":
    processa_episodi()
