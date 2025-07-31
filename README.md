<img width="1920" height="982" alt="Antarmuka Chatbot Assistant MinPo" src="https://github.com/user-attachments/assets/4b18d120-9d12-4a2c-8bb5-6f13968d28d9" /># Chatbot Assistant Minpo

Chatbot Assistant Minpo adalah asisten virtual interaktif yang dirancang untuk memberikan informasi dan melayani pertanyaan seputar Dinas Komunikasi dan Informatika (Kominfo) Kabupaten Temanggung, serta layanan-layanan yang tersedia di Mal Pelayanan Publik (MPP) Kabupaten Temanggung. Aplikasi ini bertujuan untuk mempermudah masyarakat dalam mengakses informasi dan mengajukan pertanyaan terkait layanan pemerintahan daerah.

## Fitur Utama

* **Informasi Kominfo Temanggung**: Menyediakan detail tentang profil, tugas pokok dan fungsi (tupoksi), visi-misi, dan bidang-bidang kerja Dinas Kominfo Temanggung.
* **Layanan Kominfo**: Menjelaskan berbagai layanan yang disediakan oleh Kominfo, termasuk pengelolaan informasi publik, e-government, jaringan, persandian, dan statistik.
* **Daftar OPD Temanggung + Sistem Informasi**: Menampilkan daftar 29 Organisasi Perangkat Daerah (OPD) di Kabupaten Temanggung lengkap dengan tautan sistem informasi, slogan, alamat, dan kontak mereka.
* **Layanan Mal Pelayanan Publik (MPP)**: Memberikan informasi lengkap mengenai berbagai layanan yang tersedia di MPP, seperti perizinan OSS, IMB, reklame, trayek, kesehatan, tata ruang, dan banyak lagi, beserta persyaratan dokumen yang dibutuhkan.
* **Pengaduan Warga Umum (WAGE)**: Mengarahkan pengguna ke portal WAGE untuk pelaporan masalah umum (misalnya, jalan rusak, penerangan jalan, gangguan masyarakat, bencana alam).
* **Aduan Aplikasi & Sistem (Helpdesk)**: Memberikan panduan untuk melaporkan kendala aplikasi dan sistem yang dikelola oleh Kominfo Temanggung melalui portal Helpdesk.
* **Aduan Dokumen PPID**: Mengarahkan pengguna untuk menyampaikan aduan terkait dokumen melalui Layanan Aduan PPID Kabupaten Temanggung.
* **Antarmuka Pengguna Interaktif**: Chatbot dengan tampilan yang bersih dan mudah digunakan.
* **Dukungan Markdown**: Pesan dari bot dapat dirender menggunakan Markdown untuk format yang lebih rapi dan mudah dibaca.
* **Penyimpanan Riwayat Chat**: Integrasi dengan MySQL untuk menyimpan riwayat percakapan.

## Teknologi yang Digunakan

* **Backend**:
    * Python 3
    * Flask
    * Google Gemini (sebagai model AI)
    * MySQL (untuk penyimpanan data chat)
    * `python-dotenv` (untuk mengelola environment variables)
    * `gunicorn` (untuk deployment produksi)
* **Frontend**:
    * HTML5
    * CSS3
    * JavaScript
    * Font Awesome (untuk ikon)
    * Markdown-it (untuk merender Markdown di frontend)
    * Prism.js (untuk syntax highlighting, jika ada kode dalam respon bot)

## Struktur Proyek

```
ChatbotMysql/
├── .venv/                      \# Lingkungan virtual (diabaikan oleh Git)
├── static/
│   ├── script.js               \# Logika frontend JavaScript
│   └── styles.css              \# Styling aplikasi
├── templates/
│   └── index.html              \# Halaman utama aplikasi (frontend)
├── .env                        \# File konfigurasi environment variables (SENSITIF, diabaikan oleh Git)
├── app.py                      \# Backend aplikasi Flask
├── instruksi.txt               \# Instruksi atau persona untuk chatbot
├── requirements.txt            \# Daftar dependensi Python
└── README.md                   \# File ini
```

## Persyaratan Sistem

* Python 3.8+ (tepatnya 3.10)
* MySQL Server
* Koneksi internet untuk mengakses Google Gemini API

## Instalasi dan Setup (Lokal)

Ikuti langkah-langkah berikut untuk menjalankan aplikasi ini di lingkungan lokal Anda:

1.  **Clone Repositori**:

2.  **Buat Lingkungan Virtual**:
    ```bash
    python -m venv .venv
    ```

3.  **Aktifkan Lingkungan Virtual**:
    * **Windows**:
        ```bash
        .venv\Scripts\activate
        ```
        jika belum berhasil
        ```bash
        .venv\Scripts\Activate.fish
        ```

    * **macOS/Linux**:
        ```bash
        source .venv/bin/activate
        ```

4.  **Instal Dependensi Python**:
    ```bash
    pip install -r requirements.txt
    ```
    atau
    
    ```bash
    pip install google-genai flask flask-cors mysql-connector-python dotenv 
    ```

5.  **Konfigurasi Database MySQL**:
    * Pastikan Anda memiliki server MySQL yang berjalan.
    * Buat database baru (misalnya `chatbot`).
    * Aplikasi akan secara otomatis membuat tabel `chats` jika belum ada.

6.  **Konfigurasi Environment Variables**:
    * Buat file `.env` di direktori root proyek Anda (`ChatbotMysql/`).
    * Buat API key gemini di `https://aistudio.google.com/apikey`
    * Isi file `.env` dengan kredensial API dan database Anda:
        ```env
        GENAI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
        MYSQL_HOST="localhost"
        MYSQL_USER="your_mysql_user"
        MYSQL_PASSWORD="your_mysql_password"
        MYSQL_DATABASE="chatbot"
        MYSQL_PORT="3306"
        ```
    * Ganti nilai *placeholder* dengan informasi yang sesuai.

7.  **Jalankan Aplikasi Flask**:
    ```bash
    python app.py
    ```
    Aplikasi akan berjalan di `http://127.0.0.1:5000`.

8.  **Akses Frontend**:
    Buka browser Anda dan navigasikan ke `http://127.0.0.1:5000`.
