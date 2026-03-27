# Product Requirements Document

## InsightCap

Versi: Draft 0.1  
Status: Working Draft  
Bahasa Dokumen: Indonesia (working draft)

## Important Notes

- Development utama dilakukan menggunakan Apple Silicon M4.
- Referensi awal proyek mengacu pada post X dari HuggingModels: `https://x.com/HuggingModels/status/2036874146077131225`.
- Bahasa kerja proyek adalah English untuk kode, penamaan, dokumentasi, API contract, dan antarmuka produk.
- Bahasa percakapan pada chat session ini tetap menggunakan Bahasa Indonesia.

## 1. Ringkasan Produk

**InsightCap** adalah sistem *video understanding* dan *captioning* untuk menganalisis video lalu menghasilkan deskripsi teks terhadap aktivitas, objek, kejadian, atau anomali yang muncul di dalam video. Produk ini dirancang untuk mendukung dua mode utama:

- analisis video file statis
- *live captioning* dari aliran kamera atau video streaming

InsightCap ditujukan sebagai fondasi modular yang dapat dikembangkan bertahap dari *core engine* Python, ke layer API, lalu ke antarmuka web.

## 2. Latar Belakang dan Masalah

Banyak kebutuhan pemantauan visual masih bergantung pada observasi manual. Proses ini lambat, sulit diskalakan, dan tidak menghasilkan catatan tekstual yang mudah dicari atau diintegrasikan ke sistem lain. InsightCap dibangun untuk menjawab kebutuhan tersebut dengan:

- mengubah video menjadi deskripsi tekstual yang lebih mudah dikonsumsi
- membantu analisis kejadian tanpa harus meninjau ulang video secara penuh
- menyediakan arsitektur yang cukup ringan untuk prototipe cepat dan cukup modular untuk produksi

## 3. Tujuan Produk

### Tujuan Utama

- Membangun *pipeline* efisien untuk ekstraksi frame video dan inferensi model vision-language.
- Menghasilkan caption/deskripsi aktivitas dengan halusinasi teks seminimal mungkin.
- Menyediakan arsitektur modular `Engine -> API -> Web` agar mudah diintegrasikan ke sistem lain.

### Tujuan Non-Fungsional

- Latensi serendah mungkin untuk kebutuhan near real-time.
- Penggunaan resource yang terkontrol agar tidak mudah menyebabkan OOM.
- Portabilitas antara environment development dan production.

## 4. Target Pengguna

### Pengguna Utama

- analis data visual
- system integrator
- tim operasional yang membutuhkan log kejadian berbasis video

### Pengguna Akhir

- pengguna yang ingin mengunggah video dan menerima ringkasan aktivitas secara otomatis
- operator yang membutuhkan *live captioning* dari kamera/webcam

## 5. Use Cases Utama

- Mengunggah file video lalu mendapatkan deskripsi aktivitas utama.
- Menganalisis klip pendek untuk mendeteksi objek, aksi, atau anomali.
- Menerima caption secara bertahap dari aliran video real-time.
- Mengekspor hasil caption ke format terstruktur seperti CSV atau JSON.

## 6. Ruang Lingkup

### In Scope

- analisis video file lokal seperti `.mp4` dan `.avi`
- ekstraksi frame menggunakan OpenCV
- inferensi multimodal berbasis model Qwen
- antarmuka CLI untuk fase awal
- API untuk integrasi sistem
- web app untuk upload video dan menampilkan hasil caption

### Out of Scope untuk MVP

- pelatihan/fine-tuning model dari nol
- sistem autentikasi pengguna yang kompleks
- manajemen multi-tenant
- penyimpanan video skala besar
- dashboard analitik enterprise

## 7. Kebutuhan Fungsional

### Fase 1: Core Engine

- Sistem dapat membaca file video lokal.
- Sistem dapat mengekstrak frame secara periodik atau berbasis *key sampling*.
- Sistem dapat menyusun prompt dari urutan frame yang telah diekstrak.
- Sistem dapat menghasilkan caption teks dari video.
- Sistem menyediakan CLI untuk menjalankan analisis dari terminal.

### Fase 2: API Layer

- Sistem menyediakan endpoint `POST /analyze` untuk analisis video.
- Sistem mendukung *streaming response* untuk hasil caption bertahap.
- Sistem mendukung koneksi WebSocket untuk skenario *live captioning*.

### Fase 3: Web App

- Pengguna dapat mengunggah video melalui browser.
- Pengguna dapat memutar video sambil melihat panel caption.
- Pengguna dapat melihat pembaruan hasil secara langsung.
- Pengguna dapat mengekspor hasil analisis ke CSV atau JSON.

## 8. Kebutuhan Non-Fungsional

- Sistem harus modular agar komponen engine, API, dan UI dapat dikembangkan terpisah.
- Sistem harus mampu berjalan di environment development macOS dan production Linux.
- Sistem harus memiliki strategi fallback device: `mps` -> `cuda` -> `cpu` sesuai environment.
- Sistem harus menjaga konsumsi VRAM/RAM agar stabil untuk klip pendek.
- Struktur kode harus mudah dipindahkan dari prototipe ke deployment containerized.

## 9. Pendekatan Teknis

### 9.1 Alur Pemrosesan Video

Video tidak diumpankan langsung sebagai file mentah ke LLM. Pipeline yang direncanakan:

1. baca video menggunakan OpenCV
2. lakukan sampling frame secara berkala atau berbasis strategi tertentu
3. susun frame berurutan sebagai konteks visual
4. bangun prompt yang menjelaskan tugas model
5. kirim ke model multimodal untuk menghasilkan caption

### 9.2 Strategi Inference

Untuk produksi, *inference engine* yang diprioritaskan adalah **vLLM** karena lebih baik dalam *throughput* dan efisiensi memori pada GPU NVIDIA. Untuk development lokal di Mac, pendekatan perlu disesuaikan karena vLLM bukan opsi utama pada Apple Silicon.

### 9.3 Prompting

Prompt harus menekankan:

- urutan waktu antar frame
- aktivitas utama yang sedang terjadi
- objek penting yang muncul
- pengurangan halusinasi atau asumsi yang tidak didukung visual

Contoh arah prompt:

> Analisis urutan frame video ini secara kronologis. Jelaskan aktivitas utama, objek penting, dan kejadian menonjol yang benar-benar terlihat. Hindari menebak hal yang tidak tampak.

## 10. Tech Stack

### Model AI

- `Qwen/Qwen3.5-0.8B` atau varian vision-language yang kompatibel

### Video Processing

- OpenCV (`opencv-python`)

### Backend/API

- Python 3.10+
- FastAPI
- Uvicorn

### Frontend

- Streamlit untuk MVP
- React atau Vue untuk fase produksi jika diperlukan UI yang lebih fleksibel

### Inference Runtime

#### Development

- Hugging Face Transformers dengan backend `mps`
- MLX atau `llama.cpp` sebagai opsi eksplorasi/fallback untuk Apple Silicon

#### Production

- vLLM pada Linux dengan GPU NVIDIA

### Environment

#### Development

- macOS
- Python `venv`

#### Production

- Linux Ubuntu
- Docker

## 11. Arsitektur Solusi

### Layer 1: Core Engine

Tanggung jawab:

- membaca video
- ekstraksi frame
- preprocessing
- penyusunan prompt
- inferensi caption

### Layer 2: API

Tanggung jawab:

- menerima request dari sistem lain
- mengelola upload video
- mengembalikan hasil sinkron atau streaming
- mengatur antrean inferensi

### Layer 3: Web App

Tanggung jawab:

- upload video
- menampilkan video player
- menampilkan hasil caption
- menyediakan ekspor hasil

## 12. Roadmap dan Milestone

### Fase 1: Core Python Engine

#### Deliverables

- modul pembaca video
- modul ekstraksi frame
- modul prompt engine
- modul inferensi
- CLI tool

#### Kriteria Sukses

- model dapat dimuat di environment development
- klip video 10 detik dapat dianalisis tanpa OOM
- hasil caption dasar dapat dihasilkan dari terminal

### Fase 2: API Layer dan Integrasi

#### Deliverables

- endpoint `POST /analyze`
- *streaming response*
- WebSocket untuk *live captioning*

#### Kriteria Sukses

- inferensi dapat diakses melalui jaringan
- request paralel tidak merusak antrean resource GPU
- hasil dapat diterima bertahap oleh klien

### Fase 3: Web App

#### Deliverables

- halaman upload video
- tampilan video + caption panel
- ekspor CSV/JSON

#### Kriteria Sukses

- seluruh alur penggunaan dapat dilakukan via browser
- pengguna non-teknis tidak perlu berinteraksi dengan terminal atau backend

## 13. Risiko dan Pertimbangan Teknis

- Pemilihan model vision-language harus dipastikan benar-benar kompatibel dengan kebutuhan input frame.
- Sampling frame yang terlalu rapat akan meningkatkan biaya komputasi dan risiko OOM.
- Sampling frame yang terlalu jarang dapat menurunkan kualitas pemahaman aktivitas.
- Development di Mac dan production di Linux/NVIDIA membutuhkan abstraksi device yang bersih.
- *Live captioning* memerlukan desain antrean dan streaming yang stabil agar latensi tetap terkendali.

## 14. Keputusan Teknis Awal

- Untuk development lokal, gunakan `venv`, bukan Conda.
- Untuk device inference, deteksi prioritas: `mps` di Mac, `cuda` di Linux GPU, lalu `cpu` sebagai fallback.
- Untuk MVP, fokus pada file video statis terlebih dahulu sebelum mengoptimalkan *live captioning*.
- Untuk UI awal, prioritaskan Streamlit agar validasi produk bisa dilakukan cepat.

## 15. Langkah Memulai Fase 1

### 15.1 Menyiapkan Environment

```bash
mkdir InsightCap
cd InsightCap
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
```

### 15.2 Instalasi Dependensi Inti

```bash
pip install opencv-python transformers torch torchvision
pip install mlx
```

Catatan:

- `mlx` bersifat opsional, tetapi layak dicoba untuk optimasi di Apple Silicon.
- Paket inference final untuk production dapat berbeda saat berpindah ke Linux + NVIDIA.

### 15.3 Uji Device MPS

Buat file `test_mps.py`:

```python
import torch

if torch.backends.mps.is_available():
    print("Metal (MPS) siap digunakan! Inference akan dipercepat.")
else:
    print("MPS tidak terdeteksi, akan menggunakan CPU.")
```

Lalu jalankan:

```bash
python test_mps.py
```

## 16. Catatan Implementasi MVP

Urutan eksekusi yang direkomendasikan:

1. bangun CLI untuk analisis video file
2. validasi kualitas sampling frame dan prompt
3. bungkus engine ke FastAPI
4. tambahkan mode streaming/WebSocket
5. buat UI Streamlit untuk validasi pengguna

## 17. Asumsi yang Masih Perlu Dikonfirmasi

- model vision-language final yang akan dipakai
- definisi output caption: per video, per segmen waktu, atau per event
- target latensi untuk mode real-time
- target hardware production yang benar-benar akan digunakan
