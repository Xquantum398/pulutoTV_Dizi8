import os
import requests

# GitHub Actions'ta ayarlayacağımız Secret'tan sunucu adresini alacak
# Örneğin: https://kullanici-adi-space-adi.hf.space
APP_URL = os.environ.get("https://pulutotv-tofask.hf.space")

if not APP_URL:
    print("HATA: MY_APP_URL adresi bir 'secret' olarak ayarlanmamış!")
    exit(1)

try:
    with open("links_to_warm.txt", "r") as f:
        stream_ids = [line.strip() for line in f if line.strip()]
    
    if not stream_ids:
        print("UYARI: 'links_to_warm.txt' dosyası boş.")
        exit(0)

    print(f"Önbellek ısıtma işlemi başladı. Toplam {len(stream_ids)} link ziyaret edilecek...")
    
    success_count = 0
    failed_links = []

    for stream_id in stream_ids:
        # /play/ID.m3u8 formatında tam URL'yi oluştur
        url_to_ping = f"{APP_URL}/play/{stream_id}.m3u8"
        try:
            # Sadece isteğin gidip cache'i tetiklemesi yeterli, timeout kısa olabilir
            response = requests.get(url_to_ping, timeout=30)
            if response.status_code == 200:
                print(f"  [BAŞARILI] -> {stream_id}")
                success_count += 1
            else:
                print(f"  [BAŞARISIZ] -> {stream_id} (HTTP Durum Kodu: {response.status_code})")
                failed_links.append(stream_id)
        except requests.exceptions.RequestException as e:
            print(f"  [HATA] -> {stream_id} (İstek gönderilemedi: {e})")
            failed_links.append(stream_id)
    
    print("\nİşlem tamamlandı.")
    print(f"Başarılı: {success_count}/{len(stream_ids)}")
    if failed_links:
        print(f"Başarısız olan link ID'leri: {failed_links}")

except FileNotFoundError:
    print("HATA: 'links_to_warm.txt' dosyası projenin ana dizininde bulunamadı!")
    exit(1)