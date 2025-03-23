import requests
import time
import json
from bs4 import BeautifulSoup

class SuperVideoUploader:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://supervideo.cc/api/"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://supervideo.cc/"
        })
        self.session.cookies.update({
            "xfsts": "06we6yy56eiou0yj",
            "login": "axelfire",
            "cf_clearance": "zTduQgYnG1i1CAQhtcNq3OrfDO2_i5WerIc8Hx19Wh4-1742725919-1.2.1.1-tH5.B4mRsx.AU0Pa9yb3EEJmMqUY5p2YPkH21z64BimWoWX6nU1mHcGLWQ2Isd1LF6bih3qxEqcY.t5obM60IkiBf9YyV8.cHms5RzmyIFnudHmlTIuLLnA_vXEfgj_WDpY4K1k_R41ZS_ssBhWHOKeDYPagkG9eOgA3.ym6sU.59YfZbyoN2OwleGGZnOKy.MHU2ITNFmz3J1H_likxLrw6tWwwqNG.ilPRCZojnnGg_VSMHL1CXSawACorTDVPVsXOF9V3v14tlXL7MEiJJ43Vuc_O8LawUoYbgbyidthcOg_1jKDu.VFRsC3HeLIG9feosdDUZyFNroJXTQ01bj0PuelEgyES1Scf3PYAbak"
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
        """Analizza la risposta HTML/JSON per estrarre errori o filecode"""
        try:
            data = json.loads(response_text)
            if data.get("status") == 200:
                return data["result"]["filecode"]
            return data.get("msg", "Errore sconosciuto")
        
        except json.JSONDecodeError:
            soup = BeautifulSoup(response_text, 'html.parser')
            error = soup.find('textarea', {'name': 'st'})
            if error:
                return f"ERRORE SERVER: {error.text}"
            return "Risposta non riconosciuta dal server"

    def verify_upload(self, filecode, max_retries=10):
        """Verifica lo stato dell'upload con più tentativi"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.base_url}file/info",
                    params={"key": self.api_key, "file_code": filecode},
                    timeout=15
                )
                data = response.json()
                
                if data.get("result", [{}])[0].get("status") == 200:
                    return {
                        "filecode": filecode,
                        "url": f"https://supervideo.cc/{filecode}",
                        "details": data["result"][0]
                    }
                
                time.sleep(2 ** attempt)
                
            except Exception as e:
                print(f"⚠️ Tentativo {attempt + 1} fallito: {str(e)}")
        
        return None

# Configurazione
API_KEY = "22536ntvhqgnfbfdf6exk"
FILE_PATH = "video.mp4"

if __name__ == "__main__":
    uploader = SuperVideoUploader(API_KEY)
    
    try:
        print("🔄 Ottenimento server di upload...")
        server_url = uploader.get_upload_server()
        print(f"✅ Server: {server_url}")

        print("🚀 Avvio upload...")
        result = uploader.upload_file(server_url, FILE_PATH)
        
        if "ERRORE" in result:
            print(f"❌ Errore durante l'upload: {result}")
        else:
            print(f"📦 Risposta server: {result}")
            
            print("🔍 Verifica stato avanzata...")
            verification = uploader.verify_upload(result)
            
            if verification:
                print(f"🎉 Upload confermato!\n{json.dumps(verification, indent=2)}")
            else:
                print("⚠️ Upload non verificato dopo massimi tentativi")

    except Exception as e:
        print(f"🔥 Errore critico: {str(e)}")
