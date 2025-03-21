import requests
from pymongo import MongoClient

# Impostazioni MongoDB
MONGO_URI = "mongodb+srv://admin:Furkan10@miraculousitalia.cbpsh.mongodb.net/MiraculousItalia?retryWrites=true&w=majority"
DATABASE_NAME = "MiraculousItalia"
COLLECTION_NAME = "episodes"

# API Config
SUPERVIDEO_API_KEY = "22536ntvhqgnfbfdf6exk"
SUPERVIDEO_UPLOAD_URL = "https://supervideo.cc/api/upload/url"
DROPLOAD_WORKER_BASE = "https://miraep.axelfireyt10.workers.dev/?file_code="

# Folder IDs
FOLDER_IDS = {
    1: 28351,  # s1
    2: 28352,  # s2
    3: 28353,  # s3
    4: 28354,  # s4
    5: 28355   # s5
}

# Connessione MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
episodes_collection = db[COLLECTION_NAME]

def estrai_file_code(video_url):
    return video_url.split("/")[-1] if video_url else None

def upload_via_url(file_code, season, episode):
    """Utilizza l'API Upload by URL di SuperVideo"""
    worker_url = f"{DROPLOAD_WORKER_BASE}{file_code}"
    
    params = {
        "key": SUPERVIDEO_API_KEY,
        "url": worker_url,
        "adult": 0
    }

    try:
        response = requests.get(SUPERVIDEO_UPLOAD_URL, params=params)
        data = response.json()
        
        if data.get("status") == 200:
            return data.get("result", {}).get("filecode")
        print("Errore nell'upload:", data)
    except Exception as e:
        print("Errore durante l'upload:", str(e))
    
    return None

def sposta_file_nella_cartella(file_code, folder_id):
    params = {
        "key": SUPERVIDEO_API_KEY,
        "file_code": file_code,
        "fld_id": folder_id
    }
    
    try:
        response = requests.get("https://supervideo.cc/api/file/set_folder", params=params)
        return response.json().get("status") == 200
    except Exception as e:
        print("Errore nello spostamento:", str(e))
        return False

def processa_episodi():
    for episodio in episodes_collection.find():
        video_url = episodio.get("videoUrl")
        season = episodio.get("season")
        episode_num = episodio.get("episodeNumber")
        
        if not video_url or season not in FOLDER_IDS:
            continue

        file_code = estrai_file_code(video_url)
        if not file_code:
            continue

        print(f"🚀 Processing {episodio.get('slug')}...")
        
        # Upload diretto via URL
        supervideo_code = upload_via_url(file_code, season, episode_num)
        
        if supervideo_code:
            print(f"✅ Upload completato: {supervideo_code}")
            if sposta_file_nella_cartella(supervideo_code, FOLDER_IDS[season]):
                print("📁 File spostato correttamente")
            else:
                print("❌ Errore nello spostamento")
        else:
            print("❌ Upload fallito")

if __name__ == "__main__":
    processa_episodi()
