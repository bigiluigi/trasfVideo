import requests
import os
import sys
import time
import magic
from pymongo import MongoClient
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurazione MongoDB
MONGO_URI = "mongodb+srv://admin:Furkan10@miraculousitalia.cbpsh.mongodb.net/MiraculousItalia?retryWrites=true&w=majority"
DATABASE_NAME = "MiraculousItalia"
COLLECTION_NAME = "episodes"

# Configurazione API
DROPLOAD_WORKER_BASE = "https://miraep.axelfireyt10.workers.dev/"
SUPERVIDEO_API_KEY = "22536ntvhqgnfbfdf6exk"
SUPERUPLOAD_URL = "https://hfs305.serversicuro.cc/upload/01"
SUPERVIDEO_SET_FOLDER_URL = "https://supervideo.cc/api/file/set_folder"
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
    # Il titolo usato in upload non contiene l'estensione, quindi usiamo "IT{season}{episode}"
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
    """
    Recupera il filecode cercando il file per nome tramite l'API di SuperVideo.
    Viene rimosso l'estensione dal file_name perché l'API restituisce il titolo senza estensione.
    """
    base_name = file_name.rsplit(".", 1)[0]
    params = {
        "key": SUPERVIDEO_API_KEY,
        "page": 1,
        "per_page": 50
    }
    try:
        response = requests.get(SUPERVIDEO_FILE_LIST_URL, params=params)
        data = response.json()
        result = data.get("result", {})
        files = result.get("files", [])
        if not isinstance(files, list):
            print("❌ Il campo 'files' non è una lista:", files)
            return None
        for item in files:
            # Confronta il titolo (senza estensione) col base_name
            if item.get("title") == base_name:
                return item.get("file_code")
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

def process_episode(episodio):
    """
    Processa un singolo episodio: scarica, carica su SuperVideo e sposta nella cartella corretta.
    Se l'episodio appartiene alla stagione 1 ed è compreso tra 17 e 26, viene saltato.
    """
    try:
        video_url = episodio.get("videoUrl")
        season = episodio.get("season")
        episode = episodio.get("episodeNumber")
        title = episodio.get("slug", episodio.get("title", "Episodio"))

        # Salta gli episodi già processati per la stagione 1 (episodi 17-26)
        if season == 1 and 17 <= int(episode) <= 26:
            print(f"⏩ Salto {title} (episodio già processato)")
            return

        if not video_url or season not in FOLDER_IDS:
            print(f"⚠️ Episodio {title} non valido.")
            return

        file_code = estrai_file_code(video_url)
        if not file_code:
            print(f"⚠️ Impossibile estrarre file code per {video_url}")
            return

        worker_url = f"{DROPLOAD_WORKER_BASE}?file_code={file_code}"
        file_name = genera_nome_file(season, episode)
        print(f"📂 Processando {title} → {file_name}")
        print(f"🔗 URL Worker: {worker_url}")

        file_path = scarica_file(worker_url, file_name)
        if not file_path:
            print(f"❌ Download fallito per {title}.")
            return

        supervideo_file_code = upload_to_supervideo(file_path, file_name)
        if not supervideo_file_code:
            print(f"❌ Upload fallito per {title}.")
            os.remove(file_path)
            return

        folder_id = FOLDER_IDS[season]
        sposta_file_nella_cartella(supervideo_file_code, folder_id)
        os.remove(file_path)
        print(f"🗑️ File locale eliminato: {file_path}")
        time.sleep(5)
    except Exception as e:
        print(f"🔥 Errore durante il processing di {episodio.get('slug', episodio.get('title'))}: {e}")

def processa_episodi_concurrent(max_workers=6):
    """Processa gli episodi in modo concorrente con un massimo di 'max_workers' thread."""
    # Recupera tutti gli episodi dal database
    episodi = list(episodes_collection.find())
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_episode, episodio) for episodio in episodi]
        for future in as_completed(futures):
            # Se necessario, qui possiamo gestire eventuali errori provenienti dalle future.
            try:
                future.result()
            except Exception as e:
                print(f"🔥 Errore in un thread: {e}")

if __name__ == "__main__":
    processa_episodi_concurrent(max_workers=6)
    print("✅ Tutti gli episodi sono stati processati. Il processo verrà ora terminato.")
    sys.exit(0)
