import requests
from urllib.parse import quote

API_KEY = "22616t8ph32ym3c0ueibe"
FILE_CODE = "0n763ple7cdt"  # Sostituisci con il codice reale

def test_upload():
    try:
        # 1. Costruisci l'URL SENZA codificare il parametro file_code
        worker_url = f"https://miraep.axelfireyt10.workers.dev/?file_code={FILE_CODE}"
        
        # 2. Codifica SOLO l'URL completo mantenendo i caratteri speciali del worker
        encoded_url = quote(worker_url, safe=':/?&=')
        
        # 3. Parametri della richiesta
        params = {
            'key': API_KEY,
            'url': encoded_url,
            'adult': 0
        }
        
        # 4. Invia la richiesta
        response = requests.get(
            "https://supervideo.cc/api/upload/url",
            params=params,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        print("URL inviato:", response.request.url)
        print("Risposta API:", response.json())

    except Exception as e:
        print(f"Errore: {str(e)}")

if __name__ == "__main__":
    test_upload()
