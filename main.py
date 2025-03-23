import requests

def upload_file(file_path):
    url = "https://hfs305.serversicuro.cc/upload/01"
    
    with open(file_path, 'rb') as f:
        files = {
            'api_key': (None, '22536ntvhqgnfbfdf6exk'),  # Nome campo ESATTO dal form
            'file': (f.name, f, 'video/mp4')  # Mantieni lo stesso nome del campo "file"
        }
        
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            print("✅ Upload riuscito!")
            print("Risposta server:", response.text)
        else:
            print("❌ Errore HTTP:", response.status_code)
            print("Dettagli errore:", response.text)

# Utilizzo
upload_file("video.mp4")
