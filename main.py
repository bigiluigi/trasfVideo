import sys
import time
import requests
import random
import string
from pymongo import MongoClient
from urllib.parse import urlparse
from datetime import datetime
from tqdm import tqdm  # Per la barra di avanzamento

# Configurazione
DROPLOAD_WORKER = "https://miraep.axelfireyt10.workers.dev/?file_code="
SUPERVIDEO_UPLOAD_URL = "https://hfs305.serversicuro.cc/upload/01"
API_KEY = "22536ntvhqgnfbfdf6exk"
MONGO_URI = "mongodb+srv://admin:Furkan10@miraculousitalia.cbpsh.mongodb.net/MiraculousItalia?retryWrites=true&w=majority"
MAX_RETRIES = 3
DELAY_BETWEEN_UPLOADS = 10

# Mappatura cartelle
FOLDER_IDS = {
    1: 28351,  # s1
    2: 28352,  # s2
    3: 28353,  # s3
    4: 28354,  # s4
    5: 28355   # s5
}

class VideoMigrator:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client.MiraculousItalia
        self.collection = self.db.episodes
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })
        self.total_episodes = self.collection.count_documents({})
        self.processed = 0

    @staticmethod
    def genera_nome_file(season, episode):
        """Genera nome file nel formato IT{season}{episode}_random.mp4"""
        suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"IT{season}{str(episode).zfill(2)}_{suffix}.mp4"

    def scarica_video(self, file_code):
        """Scarica il video dal worker Cloudflare"""
        url = f"{DROPLOAD_WORKER}{file_code}"
        for _ in range(MAX_RETRIES):
            try:
                response = self.session.get(url, stream=True, timeout=15)
                if response.status_code == 200:
                    return response.content
            except Exception as e:
                print(f"⚠️ Errore download {file_code}: {str(e)}")
            time.sleep(5)
        return None

    def carica_video(self, file_content, file_name, season):
        """Carica il video su SuperVideo e sposta nella cartella"""
        for attempt in range(MAX_RETRIES):
            try:
                files = {
                    'api_key': (None, API_KEY),
                    'file': (file_name, file_content, 'video/mp4')
                }
                
                response = self.session.post(
                    SUPERVIDEO_UPLOAD_URL,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    filecode = self._estrai_filecode(response.text)
                    if filecode and self._sposta_in_cartella(filecode, season):
                        return filecode
            except Exception as e:
                print(f"⚠️ Errore upload {file_name}: {str(e)}")
            
            time.sleep(DELAY_BETWEEN_UPLOADS)
        return None

    def _estrai_filecode(self, response_text):
        """Estrae il filecode dalla risposta HTML/JSON"""
        try:
            if "filecode" in response_text:
                return response_text.split('name="filecode"')[1].split('</textarea>')[0].strip()
        except Exception:
            return None

    def _sposta_in_cartella(self, filecode, season):
        """Sposta il file nella cartella della stagione"""
        fld_id = FOLDER_IDS.get(season, 28351)  # Default a s1
        params = {
            "key": API_KEY,
            "file_code": filecode,
            "fld_id": fld_id
        }
        
        try:
            response = self.session.get(
                "https://supervideo.cc/api/file/set_folder",
                params=params,
                timeout=15
            )
            return response.json().get("status") == 200
        except Exception as e:
            print(f"⚠️ Errore spostamento {filecode}: {str(e)}")
            return False

    def aggiorna_database(self, episode_id, filecode):
        """Aggiorna il record su MongoDB"""
        self.collection.update_one(
            {'_id': episode_id},
            {'$set': {
                'supervideo_code': filecode,
                'migrato_il': datetime.now()
            }}
        )

    def processa_episodi(self):
        """Processo completo di migrazione con barra di avanzamento"""
        with tqdm(total=self.total_episodes, desc="Migrazione episodi", unit="ep") as pbar:
            for episodio in self.collection.find():
                try:
                    # Salta episodi già migrati
                    if episodio.get("supervideo_code"):
                        pbar.update(1)
                        continue

                    video_url = episodio.get("videoUrl")
                    if not video_url:
                        pbar.update(1)
                        continue

                    # Estrai file code
                    file_code = urlparse(video_url).path.split('/')[-1]
                    if not file_code:
                        pbar.update(1)
                        continue

                    # Scarica video
                    video_content = self.scarica_video(file_code)
                    if not video_content:
                        print(f"❌ Download fallito: {episodio['slug']}")
                        pbar.update(1)
                        continue

                    # Prepara parametri
                    season = episodio.get("season", 1)
                    episode = episodio.get("episodeNumber", 1)
                    nome_file = self.genera_nome_file(season, episode)

                    # Carica e organizza
                    supervideo_code = self.carica_video(video_content, nome_file, season)
                    
                    if supervideo_code:
                        print(f"✅ {episodio['slug']} -> {supervideo_code}")
                        self.aggiorna_database(episodio['_id'], supervideo_code)
                    else:
                        print(f"❌ Migrazione fallita: {episodio['slug']}")

                    pbar.update(1)
                    self.processed += 1

                except Exception as e:
                    print(f"🔥 Errore critico: {episodio.get('slug', 'N/A')} - {str(e)}")
                    time.sleep(10)
                    pbar.update(1)

        # Chiudi il processo quando tutto è completato
        if self.processed == self.total_episodes:
            print("✅ Migrazione completata con successo!")
            sys.exit(0)  # Termina il processo su Koyeb

if __name__ == "__main__":
    migratore = VideoMigrator()
    print("🚀 Avvio processo di migrazione...")
    migratore.processa_episodi()
