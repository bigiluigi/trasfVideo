import requests
import time
from urllib.parse import quote

# Configurazione
API_KEY = "22616t8ph32ym3c0ueibe"
FILE_CODE = "0n763ple7cdt"  # Sostituisci con il codice reale

def test_upload():
    try:
        # 1. Costruisci l'URL codificato
        worker_url = f"https://miraep.axelfireyt10.workers.dev/?file_code={FILE_CODE}"
        encoded_url = quote(worker_url, safe='')
        
        # 2. Prepara i parametri della richiesta
        params = {
            'key': API_KEY,
            'url': encoded_url,
            'adult': 0
        }
        
        # 3. Invia la richiesta di upload
        print("⚡ Invio richiesta a SuperVideo...")
        response = requests.get(
            "https://supervideo.cc/api/upload/url",
            params=params
        )
        
        # 4. Controlla la risposta immediata
        if response.status_code != 200:
            print(f"❌ Errore HTTP: {response.status_code}")
            return
            
        data = response.json()
        if data.get('status') != 200:
            print(f"❌ Errore API: {data.get('msg', 'Unknown error')}")
            return
            
        filecode = data.get('result', {}).get('filecode')
        if not filecode:
            print("❌ Formato risposta non valido")
            return
            
        print(f"✅ Filecode temporaneo: {filecode}")
        
        # 5. Verifica finale dopo 15 secondi
        print("🕒 Attesa verifica finale (15s)...")
        time.sleep(15)
        
        verify_params = {'key': API_KEY, 'file_code': filecode}
        verify_response = requests.get(
            "https://supervideo.cc/api/file/info",
            params=verify_params
        )
        
        if verify_response.json().get('result', [{}])[0].get('status') == 200:
            print(f"🎉 Upload confermato! Link: https://supervideo.cc/{filecode}")
        else:
            print("⚠️ Upload non ancora processato, verifica manualmente più tardi")
            
    except Exception as e:
        print(f"🔥 Errore critico: {str(e)}")

if __name__ == "__main__":
    test_upload()
