import requests
import time

# Configurazione
START_ID = 840807  # ID iniziale
END_ID = 849879    # ID finale 
DELAY = 5          # Secondi tra le richieste
COOKIES = {
    "xfsts": "06we6yy56eiou0yj",
    "login": "axelfire",
    "cf_clearance": "e2aR84Q5J0g.CXjo9QYwacFEba500MnjcwnbDexA__M-1742679156-1.2.1.1-jAXzh7gX_XuGrkeCbZPUvxaByAlG4ysZ9bXg1GgenpoHngGdJPlhAaGGIhkUOsPWiDGLjLeyMjpfc7HZCXqI.O75qONiY.FvZkejNxPrZ2i2RqrXjYEP4PdlIgfQTDS3_06m3Pzonn8AqbV8GbEvj3yTf.qSsIAX5duj8DqmwpYdwcnFR6ZPMAj8_nRWE8kYQiY0EfnyPKcFQMMUWq1lGjvjgGRCCwlOM.lOpBHx9ZXor_hhKhGXEuWi4x7_TjQZECaeK1miYzILbA7HCC.NCbL3egFaIqg0zEb4xq_mMp2GMix0.DcyUZITgST9pVPefyWRZa5mH3W9sqkaGU68d8Zm3aCCYy_cAN7hQBO73Ac",
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
