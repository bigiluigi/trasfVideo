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
        # Aggiungi i cookie necessari (esempio)
        self.session.cookies.update({
            "xfsts": "06we6yy56eiou0yj",
            "login": "axelfire",
            "cf_clearance": "3l3UFDuPJ9avXJ_8j.HBKD7C0PPEDOqydy_he.ULj2w-1742724937-1.2.1.1-EOPy6_vu.iF_xusRTKwbvf6Mou9HGpLktu4nkpXzQlq6WE_8F.5cKAqiTfldCMjSnUNgwcj0YJs6Op4ZAZOcHALLhaIL4FxNmpSh_m_lB5_36vTCg_ttdWrcr.a6n7B._CGFpNx.HRvA.1pLm78qc4aFhgztveCDW8kv5p4hD42BjZKQfZj3jsjU2C8FjJOvrkRJTCIIrEMcHg0MZ9_fAWS6wLtYxdw4NZ1fib2Er6WgfLpOVtPohypEX2VdH1.SHck29OxfR9IhHTJ4v3TRmhq7FvOKoFfGynYYkyZwZnKbk07acwBUzUR6oibhh3hO.rMLd2sGp.qx43g.xMEhWHLmyreBm2AJh4HsuuLkGjs"
        })

    def _parse_upload_response(self, response_text):
        """Analizza la risposta HTML/JSON per estrarre errori o filecode"""
        try:
            # Prova a parsare come JSON
            data = json.loads(response_text)
            if data.get("status") == 200:
                return data["result"]["filecode"]
            return data.get("msg", "Errore sconosciuto")
        
        except json.JSONDecodeError:
            # Parsing HTML per messaggi di errore
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
                
                time.sleep(2 ** attempt)  # Backoff esponenziale
                
            except Exception as e:
                print(f"⚠️ Tentativo {attempt + 1} fallito: {str(e)}")
        
        return None

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
        
        if "ERRORE" in result:
            print(f"❌ Errore durante l'upload: {result}")
        else:
            print(f"📦 Risposta server: {result}")
            
            # 3. Verifica approfondita
            print("🔍 Verifica stato avanzata...")
            verification = uploader.verify_upload(result)
            
            if verification:
                print(f"🎉 Upload confermato!\n{json.dumps(verification, indent=2)}")
            else:
                print("⚠️ Upload non verificato dopo massimi tentativi")

    except Exception as e:
        print(f"🔥 Errore critico: {str(e)}")
