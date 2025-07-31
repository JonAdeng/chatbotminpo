from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import logging
import time
import re
from datetime import datetime
from google import genai
from google.genai import types
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inisialisasi Flask
app = Flask(__name__)
CORS(app)  # Mengizinkan akses dari berbagai origin (untuk frontend)

# Muat file .env
load_dotenv()

# Ambil API key dari environment variable
API_KEY = os.getenv("GENAI_API_KEY")
if not API_KEY:
    logger.error("API key tidak ditemukan. Pastikan GENAI_API_KEY diset di file .env.")
    exit(1)
client = genai.Client(api_key=API_KEY)

# Konfigurasi MySQL
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'chatbot'),
    'port': int(os.getenv('MYSQL_PORT', '3306'))
}

# Coba membuat connection pool MySQL
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="chatbot_pool",
        pool_size=5,
        **DB_CONFIG
    )
    # Ambil satu koneksi untuk membuat tabel jika belum ada
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    
    # Membuat database jika belum ada
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    cursor.execute(f"USE {DB_CONFIG['database']}")
    
    # Membuat tabel chats jika belum ada
    create_table_query = """
    CREATE TABLE IF NOT EXISTS chats (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id VARCHAR(50),
        user_input TEXT NOT NULL,
        response TEXT NOT NULL,
        timestamp DATETIME NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    cursor.execute(create_table_query)
    conn.commit()
    
    cursor.close()
    conn.close()
    
    logger.info("Berhasil terhubung ke MySQL dan memastikan tabel tersedia")
    mysql_available = True
except mysql.connector.Error as err:
    logger.error(f"Gagal terhubung ke MySQL: {err}")
    mysql_available = False

# Membaca instruksi dari file
INSTRUKSI_PATH = "instruksi.txt"  
try:
    with open(INSTRUKSI_PATH, "r", encoding="utf-8") as f:
        instruksi = f.read()
    logger.info("Berhasil membaca file instruksi")
except FileNotFoundError:
    logger.error(f"File instruksi tidak ditemukan di: {INSTRUKSI_PATH}")
    exit(1)
except Exception as e:
    logger.error(f"Terjadi kesalahan saat membaca file instruksi: {e}")
    exit(1)

# Cache untuk menyimpan waktu aktivitas terakhir setiap sesi
session_activity = {}

# Cache untuk mencegah pengiriman duplikat
request_cache = {}

def save_to_mysql(user_input, response, session_id=None):
    """Menyimpan user input dan response ke MySQL."""
    if not mysql_available:
        logger.warning("MySQL tidak tersedia, data tidak disimpan")
        return False
    
    try:
        conn = connection_pool.get_connection()
        cursor = conn.cursor()
        
        # Siapkan data yang akan disimpan
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Query SQL untuk menyimpan data chat
        if session_id:
            query = """
            INSERT INTO chats (session_id, user_input, response, timestamp) 
            VALUES (%s, %s, %s, %s)
            """
            values = (session_id, user_input, response, current_time)
        else:
            query = """
            INSERT INTO chats (user_input, response, timestamp) 
            VALUES (%s, %s, %s)
            """
            values = (user_input, response, current_time)
        
        # Eksekusi query
        cursor.execute(query, values)
        conn.commit()
        
        logger.info(f"Data berhasil disimpan ke MySQL dengan ID: {cursor.lastrowid}")
        
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        logger.error(f"Terjadi kesalahan saat menyimpan ke MySQL: {err}")
        return False

def clean_response(response_text):
    """Membersihkan respons untuk menghindari duplikasi."""
    if not response_text:
        return "Maaf, tidak ada respons dari model."
    

    paragraphs = response_text.split('\n\n')
    unique_paragraphs = []
    
    for p in paragraphs:
        if not unique_paragraphs or p != unique_paragraphs[-1]:
            unique_paragraphs.append(p)
    
    cleaned_text = '\n\n'.join(unique_paragraphs)
    

    if len(cleaned_text) >= 2 and cleaned_text[:len(cleaned_text)//2] == cleaned_text[len(cleaned_text)//2:]:
        cleaned_text = cleaned_text[:len(cleaned_text)//2]
    
    return cleaned_text.strip()

def generate_response(user_input):
    """Menghasilkan respons dari chatbot berdasarkan input pengguna."""
    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_input),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text=instruksi),
        ],
        # Parameter temperature untuk mengontrol kreativitas model
        temperature=0.5,  
    )
    try:
        logger.info("Mengirim permintaan ke model Gemini")
        start_time = time.time()
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        elapsed_time = time.time() - start_time
        logger.info(f"Respons diterima dalam {elapsed_time:.2f} detik")
        
        # Bersihkan respons untuk menghindari duplikasi
        cleaned_response = clean_response(response.text)
        
        return cleaned_response
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat berkomunikasi dengan model: {e}")
        return f"Terjadi kesalahan: {e}"

def get_request_id(data):
    """Membuat ID unik untuk request untuk mencegah duplikasi."""
    user_input = data.get("user_input", "")
    session_id = data.get("session_id", "")
    timestamp = int(time.time() / 10)  # Sama untuk request dalam window 10 detik
    return f"{session_id}:{user_input}:{timestamp}"

# Route untuk melayani halaman utama
@app.route('/')
def index():
    """Melayani halaman utama chatbot."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint untuk menerima input pengguna dan mengembalikan respons chatbot."""
    # Memeriksa tipe konten
    if request.content_type != 'application/json':
        logger.warning(f"Tipe konten tidak sesuai: {request.content_type}")
        return jsonify({"error": "Tipe konten harus application/json"}), 415
    
    # Mendapatkan data JSON
    data = request.get_json()
    logger.info(f"Data yang diterima: {data}")
    
    if not data:
        logger.warning("Menerima permintaan dengan data JSON tidak valid")
        return jsonify({"error": "Data JSON tidak valid"}), 400
    
    user_input = data.get("user_input", "").strip()
    session_id = data.get("session_id", None)
    
    if not user_input:
        logger.warning("Menerima permintaan dengan input kosong")
        return jsonify({"error": "Input tidak boleh kosong"}), 400
    
    # Mencegah duplikasi request
    request_id = get_request_id(data)
    if request_id in request_cache:
        logger.info(f"Mengembalikan respons dari cache untuk request_id: {request_id}")
        return request_cache[request_id]
    
    # Update waktu aktivitas terakhir untuk sesi ini
    if session_id:
        session_activity[session_id] = datetime.now()
    
    # Menghasilkan respons
    logger.info(f"Menerima input: '{user_input}'")
    response_text = generate_response(user_input)
    
    # Menyimpan ke MySQL
    save_result = save_to_mysql(user_input, response_text, session_id)
    if not save_result:
        logger.warning("Gagal menyimpan data ke MySQL")
    
    # Buat respons
    response_data = {
        "response": response_text,
        "timestamp": datetime.now().isoformat()
    }
    
    # Simpan ke cache
    request_cache[request_id] = jsonify(response_data)
    
    # Batasi ukuran cache
    if len(request_cache) > 100:
        # Hapus item tertua
        oldest_key = next(iter(request_cache))
        del request_cache[oldest_key]
    
    return jsonify(response_data)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint untuk memeriksa status server."""
    return jsonify({
        "status": "ok",
        "mysql_connected": mysql_available,
        "active_sessions": len(session_activity)
    })

@app.errorhandler(404)
def not_found(e):
    """Handler untuk endpoint yang tidak ditemukan."""
    return jsonify({"error": "Endpoint tidak ditemukan"}), 404

@app.errorhandler(500)
def server_error(e):
    """Handler untuk kesalahan server."""
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Terjadi kesalahan pada server"}), 500

if __name__ == "__main__":
    try:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Menjalankan server pada port {port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Gagal menjalankan server: {e}")