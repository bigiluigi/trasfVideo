import requests
import time

# Configurazione
START_ID = 841836  # ID iniziale
END_ID = 849879    # ID finale 
DELAY = 2          # Secondi tra le richieste
COOKIES = {
    "xfsts": "06we6yy56eiou0yj",
    "login": "axelfire",
    "cf_clearance": "Nme1eBDRAUEG3HaYXCCvZgxngi7bykJa2qqN.g6EMbY-1742680165-1.2.1.1-_SKFTUEgDkIjKWuHcYObOyBctEK_4P.irPURh0J1ybiyAoVN6yZAQ05RGdf.C8U1zdG0.byiK4umswsWVAPPhC4wpSOVPsWmJf7KeJOi5MPrfQg_EI59OujWBb_fmy6dSDTTPmNaup2FohnLCpHzXpjM.s0joOjtkpMuZCNWAKYFmQqI.0M7wWeH.Eg_GgGY6vM8zidLQwnMCHkZWckbqdnyLag_dmz0MJXqZjNm0aAvnyASBiWyIMHrYhWhA_dPiIpJOLijhH.fX1EWdzRedbtsVyILkPFjwfw18waWzlxHeeseriGm4y7myeXjWiH8mvHhd7hQFNK9MlfFhhdoVlkNq4b7aT6DRv4BNIexhkg",
    # Aggiungi altri cookie se necessario
}

def delete_files():
    session = requests.Session()
    session.cookies.update(COOKIES)
    
    for file_id in range(START_ID, END_ID + 1):
        url = f"https://supervideo.cc/?op=upload_url&del_id={file_id}"
        
        try:
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ ID {file_id}: Cancellazione inviata")
            else:
                print(f"❌ ID {file_id}: Errore HTTP {response.status_code}")
            
        except Exception as e:
            print(f"🔥 ID {file_id}: Errore di connessione - {str(e)}")
        
        time.sleep(DELAY)

if __name__ == "__main__":
    delete_files()
