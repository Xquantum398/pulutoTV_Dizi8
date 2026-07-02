class VavooResolver:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'okhttp/4.11.0'})
        
        # İmza önbelleği: 400 saat (1,440,000 saniye)
        # Çözülmüş link önbelleği: 300 saat (1,080,000 saniye)
        self.auth_cache = TTLCache(maxsize=10, ttl=1440000)
        self.resolved_link_cache = TTLCache(maxsize=200, ttl=1080000)
        
        self.lock = Lock()

    def getAuthSignature(self):
        """
        Vavoo'dan gelişmiş cihaz meta verileriyle kimlik doğrulama imzasını alır.
        Thread-safe (Kilit mekanizmalı) ve önbellek desteklidir.
        """
        with self.lock:
            if "auth_sig" in self.auth_cache:
                app.logger.info("Vavoo Signature CACHE HIT")
                return self.auth_cache["auth_sig"]

            app.logger.info("Yeni Vavoo imzası alınıyor (Gelişmiş Payload)...")
            headers = {
                "user-agent": "okhttp/4.11.0",
                "accept": "application/json", 
                "content-type": "application/json; charset=utf-8",
                "accept-encoding": "gzip"
            }
            # Addon utils.py dosyasından alınan tam bypass payload verisi
            data = {
                "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
                "reason": "app-blur",
                "locale": "de",
                "theme": "dark",
                "metadata": {
                    "device": {
                        "type": "Handset",
                        "brand": "google",
                        "model": "Nexus",
                        "name": "21081111RG",
                        "uniqueId": "d10e5d99ab665233"
                    },
                    "os": {
                        "name": "android",
                        "version": "7.1.2",
                        "abis": ["arm64-v8a", "armeabi-v7a", "armeabi"],
                        "host": "android"
                    },
                    "app": {
                        "platform": "android",
                        "version": "3.1.20",
                        "buildId": "289515000",
                        "engine": "hbc85",
                        "signatures": ["6e8a975e3cbf07d5de823a760d4c2547f86c1403105020adee5de67ac510999e"],
                        "installer": "app.revanced.manager.flutter"
                    },
                    "version": {
                        "package": "tv.vavoo.app",
                        "binary": "3.1.20",
                        "js": "3.1.20"
                    }
                },
                "appFocusTime": 0,
                "playerActive": False,
                "playDuration": 0,
                "devMode": False,
                "hasAddon": True,
                "castConnected": False,
                "package": "tv.vavoo.app",
                "version": "3.1.20",
                "process": "app",
                "firstAppStart": 1743962904623,
                "lastAppStart": 1743962904623,
                "ipLocation": "",
                "adblockEnabled": True,
                "proxy": {
                    "supported": ["ss", "openvpn"],
                    "engine": "ss", 
                    "ssVersion": 1,
                    "enabled": True,
                    "autoServer": True,
                    "id": "pl-waw"
                },
                "iap": {
                    "supported": False
                }
            }
            try:
                resp = self.session.post("https://www.vavoo.tv/api/app/ping", json=data, headers=headers, timeout=20)
                resp.raise_for_status()
                addon_sig = resp.json().get("addonSig")
                if addon_sig:
                    app.logger.info("Yeni Vavoo imzası başarıyla alındı ve önbelleğe kaydedildi.")
                    self.auth_cache["auth_sig"] = addon_sig
                    return addon_sig
                else:
                    app.logger.error("Vavoo API yanıtında 'addonSig' bulunamadı.")
                    return None
            except Exception as e:
                app.logger.error(f"Vavoo imzası alınırken KRİTİK HATA: {e}")
                return None

    def resolve_vavoo_link(self, link, verbose=False):
        """
        Vavoo linkini çözümler. Önbellek kontrolü yapar, imza eksikse tamamlar
        ve list/dict tipindeki tüm API yanıt varyasyonlarını güvenle parse eder.
        """
        if not link or "vavoo.to" not in link:
            return None

        if link in self.resolved_link_cache:
            app.logger.info(f"Vavoo Resolved Link CACHE HIT for: {link}")
            return self.resolved_link_cache[link]

        signature = self.getAuthSignature()
        if not signature:
            app.logger.error("İmza alınamadığı için link çözme işlemi iptal edildi.")
            return None

        headers = {
            "user-agent": "MediaHubMX/2",
            "accept": "application/json",
            "content-type": "application/json; charset=utf-8", 
            "accept-encoding": "gzip",
            "mediahubmx-signature": signature
        }
        data = {
            "language": "de",
            "region": "AT", 
            "url": link,
            "clientVersion": "3.0.2"
        }

        try:
            # Büyük akışlarda problem yaşanmaması adına timeout 45 saniye olarak tutuldu
            resp = self.session.post("https://vavoo.to/mediahubmx-resolve.json", json=data, headers=headers, timeout=45)
            resp.raise_for_status()
            result = resp.json()
            
            resolved_url = None
            if isinstance(result, list) and result and result[0].get("url"):
                resolved_url = result[0]["url"]
            elif isinstance(result, dict) and result.get("url"):
                resolved_url = result["url"]

            if resolved_url:
                app.logger.info(f"Vavoo link resolved and cached: {resolved_url}")
                self.resolved_link_cache[link] = resolved_url
                return resolved_url
            
            app.logger.warning(f"Vavoo resolution response did not contain a URL. Response: {result}")
            return None
        except Exception as e:
            app.logger.error(f"FATAL EXCEPTION during Vavoo resolution: {e}")
            return None
