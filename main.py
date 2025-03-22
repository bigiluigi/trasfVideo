import requests
import time
from urllib.parse import quote

API_KEY = "22616t8ph32ym3c0ueibe"
FILE_CODE = "0n763ple7cdt"  # Sostituisci con il codice reale
TIMEOUT = 10  # Timeout in secondi per ogni richiesta
MAX_RETRIES = 3  # Numero massimo di tentativi

def test_upload():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        # 1. Costruisci e codifica l'URL
        worker_url = f"https://miraep.axelfireyt10.workers.dev/?file_code={FILE_CODE}"
        encoded_url = quote(worker_url, safe='')

        # 2. Richiesta di upload con timeout e retry
        upload_params = {
            'key': API_KEY,
            'url': encoded_url,
            'adult': 0
        }

        print("⚡ Invio richiesta a SuperVideo...")
        
        for attempt in range(MAX_RETRIES):
            try:
                response = session.get(
                    "https://supervideo.cc/api/upload/url",
                    params=upload_params,
                    headers=headers,
                    timeout=TIMEOUT
                )
                response.raise_for_status()
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if attempt < MAX_RETRIES - 1:
                    print(f"⌛ Timeout, tentativo {attempt + 2}/{MAX_RETRIES}...")
                    time.sleep(2 ** attempt)  # Backoff esponenziale
                    continue
                else:
                    print("❌ Errore di connessione dopo massimi tentativi")
                    return

        # 3. Analisi risposta
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

        # 4. Verifica asincrona con polling
        print("🕒 Avvio verifica asincrona...")
        verify_params = {'key': API_KEY, 'file_code': filecode}
        
        for _ in range(10):  # 10 tentativi in 150 secondi
            try:
                verify_response = session.get(
                    "https://supervideo.cc/api/file/info",
                    params=verify_params,
                    headers=headers,
                    timeout=TIMEOUT
                )
                
                if verify_response.json().get('result', [{}])[0].get('status') == 200:
                    print(f"🎉 Upload confermato! Link: https://supervideo.cc/{filecode}")
                    return
                
                print("⏳ File in processing...")
                time.sleep(15)  # Intervallo tra i check
            
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                print("⌛ Timeout durante la verifica, riprovo...")
                continue

        print("⚠️ Upload non confermato dopo 150 secondi, verifica manualmente")

    except Exception as e:
        print(f"🔥 Errore critico: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    test_upload()
