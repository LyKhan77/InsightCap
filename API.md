# InsightCap API

## Nama API

**InsightCap API**

InsightCap API adalah backend untuk analisis video dan monitoring kamera RTSP berbasis vision-language model `qwen3.5:0.8b` melalui Ollama.

API ini menyediakan dua mode terpisah:

- **Video Input API** untuk analisis file video upload
- **RTSP Monitoring API** untuk monitoring kamera live melalui URL RTSP

## Fungsi API

Fungsi utama API:

- menerima file video dan menghasilkan caption frame-per-frame
- menghasilkan ringkasan akhir dari video upload
- membuat session monitoring RTSP secara live
- mengirim event caption RTSP secara real-time via WebSocket
- menyediakan preview stream RTSP yang ramah browser melalui MJPEG bridge
- menyediakan health check untuk status server dan device inferensi

## Base URL

Default local base URL:

```text
http://localhost:6060
```

Dokumentasi Swagger:

```text
http://localhost:6060/docs
```

## Menjalankan API

Aktifkan environment lalu jalankan server:

```bash
source env/bin/activate
uvicorn api.main:app --reload --port 6060
```

Sebelum menjalankan API, pastikan Ollama aktif:

```bash
ollama serve
ollama pull qwen3.5:0.8b
```

## Ringkasan Endpoint

| Method | Path | Fungsi |
|---|---|---|
| `GET` | `/` | Info dasar API |
| `GET` | `/health` | Health check + device |
| `POST` | `/api/v1/analyze` | Analisis video upload, hasil JSON penuh |
| `POST` | `/api/v1/analyze/stream` | Analisis video upload, hasil streaming SSE |
| `POST` | `/api/v1/rtsp/sessions` | Membuat session monitoring RTSP |
| `GET` | `/api/v1/rtsp/sessions` | List session RTSP |
| `GET` | `/api/v1/rtsp/sessions/{session_id}` | Detail status session RTSP |
| `DELETE` | `/api/v1/rtsp/sessions/{session_id}` | Menghentikan session RTSP |
| `GET` | `/api/v1/rtsp/sessions/{session_id}/preview.jpg` | Snapshot JPEG preview terbaru |
| `GET` | `/api/v1/rtsp/sessions/{session_id}/preview.mjpeg` | Preview live MJPEG untuk browser |
| `WS` | `/api/v1/rtsp/sessions/{session_id}/events` | Event caption live RTSP |

## Cara Menggunakan API

### 1. Health Check

Gunakan untuk memastikan API hidup dan device inferensi terdeteksi.

```bash
curl http://localhost:6060/health
```

Contoh response:

```json
{
  "status": "ok",
  "device": "mps"
}
```

### 2. Analisis Video Upload

Untuk analisis batch file video dan mendapatkan hasil akhir lengkap:

```bash
curl -X POST http://localhost:6060/api/v1/analyze \
  -F "file=@video.mp4" \
  -F "model=qwen3.5:0.8b"
```

Contoh response:

```json
{
  "caption": "A person walks into frame and interacts with objects on a desk.",
  "frame_captions": [
    "A person enters the room.",
    "The person stands near a desk.",
    "The person handles items on the desk."
  ],
  "frame_count": 3,
  "duration_seconds": 12.4,
  "device_used": "mps",
  "model_id": "qwen3.5:0.8b"
}
```

### 3. Analisis Video Upload dengan SSE

Untuk menerima event bertahap selama analisis video:

```bash
curl -X POST http://localhost:6060/api/v1/analyze/stream \
  -F "file=@video.mp4" \
  -F "model=qwen3.5:0.8b" \
  --no-buffer
```

Urutan event utama:

- `init`
- `frame`
- `summary`
- `done`

Contoh format:

```text
event: init
data: {"total_frames": 12, "video_fps": 30.0, "duration_seconds": 12.4}

event: frame
data: {"index": 0, "caption": "...", "timestamp_seconds": 0.0}

event: summary
data: {"caption": "..."}

event: done
data: {"frame_count": 12, "duration_seconds": 12.4, "device_used": "mps", "model_id": "qwen3.5:0.8b"}
```

### 4. Membuat Session RTSP

Gunakan endpoint ini untuk memulai monitoring kamera live.

```bash
curl -X POST http://localhost:6060/api/v1/rtsp/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "rtsp_url": "rtsp://user:password@camera-host/stream",
    "model": "qwen3.5:0.8b",
    "sample_every_seconds": 1.0,
    "session_name": "front-gate"
  }'
```

Contoh response:

```json
{
  "session_id": "9f4b6f6f8b0d4d6ea5e5c123456789ab",
  "session_name": "front-gate",
  "status": "running",
  "source": "rtsp://***@camera-host/stream",
  "model_id": "qwen3.5:0.8b",
  "sample_every_seconds": 1.0,
  "started_at": "2026-03-30T08:00:00+00:00",
  "last_event_at": "2026-03-30T08:00:01+00:00",
  "last_caption": null,
  "captions_emitted": 0,
  "reconnect_count": 0,
  "lag_ms": null,
  "last_error": null
}
```

### 5. Melihat Status Session RTSP

```bash
curl http://localhost:6060/api/v1/rtsp/sessions
curl http://localhost:6060/api/v1/rtsp/sessions/<session_id>
```

Field penting pada response status:

- `status`
- `captions_emitted`
- `lag_ms`
- `reconnect_count`
- `last_error`

### 6. Menghentikan Session RTSP

```bash
curl -X DELETE http://localhost:6060/api/v1/rtsp/sessions/<session_id>
```

### 7. Mengambil Preview RTSP

Snapshot JPEG terbaru:

```bash
curl http://localhost:6060/api/v1/rtsp/sessions/<session_id>/preview.jpg --output preview.jpg
```

Preview live MJPEG untuk browser:

```text
http://localhost:6060/api/v1/rtsp/sessions/<session_id>/preview.mjpeg
```

Catatan:

- preview browser memakai MJPEG bridge, bukan RTSP native
- endpoint ini cocok untuk browser, panel web, atau embed `<img>`

### 8. Subscribe Event RTSP via WebSocket

WebSocket URL:

```text
ws://localhost:6060/api/v1/rtsp/sessions/<session_id>/events
```

Event yang dapat diterima:

- `connected`
- `caption`
- `warning`
- `heartbeat`
- `stopped`
- `error`

Contoh event:

```json
{
  "event": "caption",
  "session_id": "9f4b6f6f8b0d4d6ea5e5c123456789ab",
  "emitted_at": "2026-03-30T08:00:05+00:00",
  "data": {
    "seq": 3,
    "caption": "A person stands near the entrance and looks toward the street.",
    "captured_at": "2026-03-30T08:00:04+00:00",
    "processed_at": "2026-03-30T08:00:05+00:00",
    "lag_ms": 842.2
  }
}
```

## Cara Integrasi yang Disarankan

### Untuk Sistem Upload Video

Gunakan:

- `POST /api/v1/analyze` jika hanya butuh hasil akhir
- `POST /api/v1/analyze/stream` jika butuh progress bertahap

### Untuk Sistem Monitoring Kamera

Gunakan pola ini:

1. `POST /api/v1/rtsp/sessions`
2. subscribe `WS /api/v1/rtsp/sessions/{session_id}/events`
3. gunakan `preview.mjpeg` untuk panel live stream
4. gunakan `GET /api/v1/rtsp/sessions/{session_id}` untuk polling status jika diperlukan
5. `DELETE /api/v1/rtsp/sessions/{session_id}` saat monitoring selesai

## Troubleshoot API

### 1. API tidak bisa diakses

Gejala:

- `Connection refused`
- web app menunjukkan `API_DISCONNECTED`

Pemeriksaan:

```bash
curl http://localhost:6060/health
```

Solusi:

- pastikan `uvicorn api.main:app --reload --port 6060` sedang berjalan
- pastikan port `6060` tidak dipakai service lain

### 2. Ollama belum aktif

Gejala:

- analisis gagal saat inferensi
- caption tidak keluar
- response error internal saat memanggil model

Solusi:

```bash
ollama serve
ollama pull qwen3.5:0.8b
```

### 3. RTSP session berhasil dibuat tetapi preview kosong

Gejala:

- `preview.jpg` mengembalikan `404`
- panel `LIVE_STREAM` belum menampilkan gambar

Kemungkinan:

- stream baru saja dibuat dan frame pertama belum terbaca
- URL RTSP salah
- kamera membutuhkan auth atau transport tertentu

Pemeriksaan:

```bash
curl http://localhost:6060/api/v1/rtsp/sessions/<session_id>
```

Lihat field:

- `status`
- `last_error`
- `reconnect_count`

### 4. RTSP stream lag

Gejala:

- preview terasa lambat
- caption tetap benar tetapi stream tidak halus

Kondisi implementasi saat ini:

- preview browser menggunakan MJPEG bridge
- caption dan preview sudah dipisah agar capture tidak tertahan inferensi
- tetap saja MJPEG bukan format paling efisien untuk live monitoring

Solusi praktis:

- naikkan kualitas jaringan kamera
- turunkan resolusi stream dari kamera jika memungkinkan
- naikkan `sample_every_seconds` agar beban inferensi turun
- jika butuh live stream yang lebih halus, pertimbangkan upgrade preview ke HLS atau WebRTC

### 5. RTSP caption terlambat

Gejala:

- `lag_ms` besar
- caption datang lebih lambat dari yang diharapkan

Penyebab umum:

- model inferensi lambat
- mesin tidak cukup kuat
- source RTSP beresolusi terlalu tinggi

Solusi:

- naikkan `sample_every_seconds`
- gunakan hardware yang lebih kuat
- pindah ke runtime inferensi produksi jika skala bertambah

### 6. Session RTSP sering reconnect

Gejala:

- event `warning`
- `reconnect_count` meningkat

Kemungkinan:

- jaringan kamera tidak stabil
- RTSP URL salah atau session kamera diputus
- codec/transport stream tidak cocok dengan OpenCV backend

Solusi:

- verifikasi RTSP URL di player lain seperti VLC
- cek akses user/password
- cek apakah stream memang aktif dan reachable dari mesin API

### 7. Web app berjalan tetapi RTSP panel tidak muncul

Pemeriksaan:

- pilih mode `RTSP` pada select mode page
- klik `START_MONITORING`
- pastikan session RTSP berhasil dibuat

Catatan:

- mode `VIDEO` dan `RTSP` memakai flow berbeda
- layout halaman sama, tetapi input dan sumber `LIVE_STREAM` berbeda

## Limitasi Saat Ini

- tidak ada authentication atau rate limiting
- session RTSP disimpan in-memory
- default maksimum session aktif terbatas
- preview live masih MJPEG bridge, belum HLS/WebRTC
- backend inferensi masih sequential per frame

## Lokasi Implementasi

Bagian implementasi utama:

- `api/main.py`
- `api/routes/analyze.py`
- `api/routes/rtsp.py`
- `api/rtsp_service.py`
- `api/schemas.py`
- `api/rtsp_schemas.py`

