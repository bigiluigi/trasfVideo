import requests
import time
from urllib.parse import quote

class SuperVideoUploader:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://supervideo.cc/api/"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })

    def get_upload_server(self):
        """Ottiene il server di upload dalla API"""
        try:
            response = self.session.get(
                f"{self.base_url}upload/server",
                params={"key": self.api_key, "adult": 0},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == 200:
                return data["result"]
            
            raise Exception(f"Errore API: {data.get('msg', 'Unknown error')}")
            
        except Exception as e:
            raise Exception(f"Fallito ottenimento server: {str(e)}")

    def upload_file(self, server_url, file_path):
        """Carica il file sul server specificato"""
        try:
            with open(file_path, "rb") as f:
                files = {
                    "key": (None, self.api_key),
                    "adult": (None, "0"),
                    "file": (f.name, f, "video/mp4")
                }
                
                response = self.session.post(
                    server_url,
                    files=files,
                    timeout=30
                )
                
            if response.status_code == 200:
                return self._parse_upload_response(response.text)
                
            raise Exception(f"HTTP Error: {response.status_code}")
            
        except Exception as e:
            raise Exception(f"Upload fallito: {str(e)}")

    def _parse_upload_response(self, response_text):
        """Analizza la risposta di upload (supporta JSON e HTML)"""
        try:
            # Prova a parsare come JSON
            data = requests.utils.json_loader(response_text)
            if data.get("status") == 200:
                return data["result"]["filecode"]
            
            return data.get("msg", "Unknown error")
            
        except ValueError:
            # Parsing HTML fallback
            if "upload_result" in response_text:
                return "Upload completato via redirect"
            
            return "Risposta non riconosciuta dal server"

    def verify_upload(self, filecode, max_retries=5):
        """Verifica lo stato dell'upload"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.base_url}file/info",
                    params={"key": self.api_key, "file_code": filecode},
                    timeout=10
                )
                
                data = response.json()
                if data.get("result", [{}])[0].get("status") == 200:
                    return True
                    
                time.sleep(2 ** attempt)  # Backoff esponenziale
                
            except Exception:
                continue
                
        return False

# Configurazione
API_KEY = "22536ntvhqgnfbfdf6exk"
FILE_PATH = "video.mp4"

if __name__ == "__main__":
    uploader = SuperVideoUploader(API_KEY)
    
    try:
        # 1. Ottieni il server di upload
        print("🔄 Ottenimento server di upload...")
        server_url = uploader.get_upload_server()
        print(f"✅ Server: {server_url}")
        
        # 2. Carica il file
        print("🚀 Avvio upload...")
        result = uploader.upload_file(server_url, FILE_PATH)
        
        if isinstance(result, str) and len(result) == 12:  # Formato filecode
            print(f"📦 Filecode ricevuto: {result}")
            
            # 3. Verifica finale
            print("🔍 Verifica stato...")
            if uploader.verify_upload(result):
                print(f"🎉 Upload confermato! https://supervideo.cc/{result}")
            else:
                print("⚠️ Upload non verificato, controllare manualmente")
                
        else:
            print(f"❌ Errore durante l'upload: {result}")
            
    except Exception as e:
        print(f"🔥 Errore critico: {str(e)}")
