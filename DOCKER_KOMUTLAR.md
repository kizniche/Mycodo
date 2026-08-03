# MYCODO DOCKER KOMUTLARI

## Container Yönetimi

### Başlatma/Durdurma
```bash
# Tüm container'ları başlat
docker compose up -d

# Tüm container'ları durdur
docker compose down

# Belirli bir container'ı yeniden başlat
docker compose restart mycodo_flask
docker compose restart mycodo_daemon

# Tüm container'ları yeniden başlat
docker compose restart
```

### Durum Kontrolü
```bash
# Çalışan container'ları göster
docker compose ps

# Tüm container'ları göster
docker ps -a

# Resource kullanımı
docker stats

# Volume'ları listele
docker volume ls | grep mycodo
```

### Loglar
```bash
# Tüm logları izle
docker compose logs -f

# Belirli bir container'ın loglarını izle
docker compose logs -f mycodo_flask
docker compose logs -f mycodo_daemon
docker compose logs -f mycodo_influxdb

# Son 100 satır log
docker compose logs --tail=100 mycodo_flask

# Hata logları
docker compose logs --tail=50 | grep -i error
```

## Container İçine Girme

```bash
# Flask container'ına shell ile gir
docker exec -it mycodo_flask bash

# Daemon container'ına gir
docker exec -it mycodo_daemon bash

# InfluxDB container'ına gir
docker exec -it mycodo_influxdb bash

# Python shell (Flask container içinde)
docker exec -it mycodo_flask /home/mycodo/env/bin/python
```

## Veritabanı Yönetimi

```bash
# InfluxDB shell'e gir
docker exec -it mycodo_influxdb influx

# Veritabanlarını listele (InfluxDB shell içinde)
SHOW DATABASES

# Mycodo veritabanını kullan
USE mycodo_db

# Ölçümleri listele
SHOW MEASUREMENTS
```

## Güncelleme/Rebuild

```bash
# Kod değişikliği sonrası rebuild
cd /home/user/Mycodo/docker
docker compose up --build -d

# Sadece belirli bir service'i rebuild et
docker compose up --build -d mycodo_flask

# Cache kullanmadan rebuild (tamamen sıfırdan)
docker compose build --no-cache
docker compose up -d
```

## Temizlik

```bash
# Container'ları durdur ve sil
docker compose down

# Container'ları + volume'ları sil (TÜM VERİ SİLİNİR!)
docker compose down -v

# Kullanılmayan Docker verilerini temizle
docker system prune -a

# Sadece Mycodo volume'larını sil
docker volume rm $(docker volume ls -q | grep mycodo)

# Tüm Docker verilerini temizle (DİKKAT!)
docker system prune -a --volumes
```

## Sorun Giderme

```bash
# Container sağlık durumu
docker inspect mycodo_flask | grep -A 10 Health

# Container içinde komut çalıştır
docker exec mycodo_flask ls -la /home/mycodo/

# Dosya izinlerini kontrol et
docker exec mycodo_flask ls -la /var/log/mycodo/

# Network durumu
docker network inspect docker_default

# Port kullanımı
sudo netstat -tlnp | grep -E '80|443'
```

## Grafana & Telegraf (Opsiyonel)

```bash
# docker-compose.yml'de Grafana ve Telegraf'ı aktifleştir
# (dosyada yorum satırlarını kaldır)

# Rebuild et
docker compose up --build -d

# Grafana'ya eriş
# http://localhost:3000
# Kullanıcı: admin
# Şifre: admin
```

## Backup

```bash
# Volume'ları yedekle
docker run --rm \
  -v mycodo_databases:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/mycodo_backup.tar.gz /data

# Geri yükle
docker run --rm \
  -v mycodo_databases:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/mycodo_backup.tar.gz -C /
```

## Performans İzleme

```bash
# Container resource kullanımı (canlı)
docker stats

# Bellek kullanımı
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"

# CPU kullanımı
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}"
```

## Hızlı Erişim Alias'ları

`.bashrc` veya `.zshrc` dosyanıza ekleyin:

```bash
# Mycodo Docker Alias'ları
alias mycodo-start='cd /home/user/Mycodo/docker && docker compose up -d'
alias mycodo-stop='cd /home/user/Mycodo/docker && docker compose down'
alias mycodo-restart='cd /home/user/Mycodo/docker && docker compose restart'
alias mycodo-logs='cd /home/user/Mycodo/docker && docker compose logs -f'
alias mycodo-flask='docker exec -it mycodo_flask bash'
alias mycodo-daemon='docker exec -it mycodo_daemon bash'
alias mycodo-status='cd /home/user/Mycodo/docker && docker compose ps'
alias mycodo-rebuild='cd /home/user/Mycodo/docker && docker compose up --build -d'
```

Sonra çalıştırın:
```bash
source ~/.bashrc  # veya source ~/.zshrc
```

Kullanım:
```bash
mycodo-start      # Başlat
mycodo-logs       # Logları izle
mycodo-flask      # Flask container'a gir
```

## İlk Kurulum Sonrası

1. Web arayüzüne git: https://localhost
2. Admin kullanıcı oluştur
3. Timezone'u kontrol et (Settings > General)
4. InfluxDB bağlantısını test et (Settings > Measurement)
5. İlk sensor/output ekle (Input/Output menüsünden)

## Önemli Dosya Yolları (Container İçi)

```
/home/mycodo/                          # Ana dizin
/home/mycodo/mycodo/                   # Uygulama kodu
/home/mycodo/databases/                # SQLite veritabanı
/var/log/mycodo/                       # Log dosyaları
/home/mycodo/mycodo/mycodo_flask/      # Flask uygulaması
/home/mycodo/cameras/                  # Kamera kayıtları
/var/lib/influxdb/                     # InfluxDB verileri
```
