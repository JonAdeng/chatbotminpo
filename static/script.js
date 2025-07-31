// Variabel global
let sessionId = generateSessionId();
let isConnected = false;
const API_URL = 'http://localhost:5000';  // Ganti dengan URL backend Anda
let isProcessing = false;
let requestQueue = [];

// Elemen DOM
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const statusIndicator = document.getElementById('statusIndicator');
const emptyChat = document.getElementById('emptyChat');
const newChatBtn = document.getElementById('newChatBtn');
const suggestedQuestions = document.querySelectorAll('.suggested-question');

// Tambahkan library Markdown-it
const md = window.markdownit ? window.markdownit({
    html: false,
    linkify: true,
    typographer: true
}) : null;

// Pastikan md (markdown-it instance) ada sebelum mencoba memodifikasi aturannya
if (md) {
    const defaultRender = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
        return self.renderToken(tokens, idx, options);
    };

    md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
        // Tambahkan atribut target="_blank"
        tokens[idx].attrSet('target', '_blank');
        // Tambahkan atribut rel="noopener noreferrer" untuk keamanan
        tokens[idx].attrSet('rel', 'noopener noreferrer');

        // Panggil renderer default untuk memastikan link tetap dirender seperti biasa
        return defaultRender(tokens, idx, options, env, self);
    };
}

// Fungsi untuk menghasilkan ID sesi unik
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substring(2, 15);
}

// Fungsi untuk memeriksa status koneksi ke server
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            isConnected = true;
            statusIndicator.innerHTML = '<span class="status-dot online"></span><span>Online</span>';
            sendBtn.disabled = messageInput.value.trim() === '';
        } else {
            isConnected = false;
            statusIndicator.innerHTML = '<span class="status-dot offline"></span><span>Offline</span>';
            sendBtn.disabled = true;
        }
    } catch (error) {
        console.error('Error checking server status:', error);
        isConnected = false;
        statusIndicator.innerHTML = '<span class="status-dot offline"></span><span>Offline</span>';
        sendBtn.disabled = true;
    }
}

// Fungsi untuk mengirim pesan ke server
async function sendMessage(message) {
    if (!isConnected) {
        showError('Tidak dapat mengirim pesan. Server tidak tersedia.');
        return;
    }
    
    // Buat unique request ID untuk mencegah duplikasi
    const requestId = Date.now().toString();
    
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Request-ID': requestId, // Header tambahan untuk identifikasi
            },
            body: JSON.stringify({
                user_input: message,
                session_id: sessionId,
                request_id: requestId // Parameter tambahan untuk identifikasi
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Error sending message');
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        showError('Gagal mengirim pesan. Coba lagi nanti.');
        return null;
    }
}

// Fungsi untuk menampilkan error
function showError(message) {
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    chatMessages.appendChild(errorElement);
    
    // Hapus pesan error setelah 5 detik
    setTimeout(() => {
        errorElement.remove();
    }, 5000);
}

// Fungsi untuk menambahkan pesan ke tampilan chat dengan dukungan markdown
function addMessage(text, isUser = false) {
    // Sembunyikan tampilan kosong jika ada
    if (emptyChat) {
        emptyChat.style.display = 'none';
    }

    const message = document.createElement('div');
    message.className = isUser ? 'message user-message' : 'message bot-message';
    
    // Tambahkan text dengan dukungan markdown
    const messageText = document.createElement('div');
    messageText.className = 'message-content';
    
    // Gunakan markdown-it jika tersedia dan bukan pesan pengguna
    if (md && !isUser) {
        messageText.innerHTML = md.render(text);
    } else {
        // Fallback ke metode sederhana jika markdown-it tidak tersedia
        messageText.innerHTML = text.replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>')  // Italic
            .replace(/`(.*?)`/g, '<code>$1</code>');  // Inline code
    }
    
    message.appendChild(messageText);
    
    // Tambahkan waktu
    const now = new Date();
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';
    timeElement.textContent = now.toLocaleTimeString();
    message.appendChild(timeElement);
    
    chatMessages.appendChild(message);
    
    // Scroll ke bawah
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fungsi untuk menampilkan indikator "Mengetik..."
function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fungsi untuk menghapus indikator "Mengetik..."
function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// Event listener untuk input pesan
messageInput.addEventListener('input', () => {
    sendBtn.disabled = messageInput.value.trim() === '' || !isConnected;
});

// Event listener untuk tombol kirim
sendBtn.addEventListener('click', () => {
    handleSendMessage();
});

// Event listener untuk enter key
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        handleSendMessage();
    }
});

// Fungsi untuk menangani pengiriman pesan
async function handleSendMessage() {
    const message = messageInput.value.trim();
    if (message === '' || !isConnected) return;
    
    // Tambahkan pesan ke antrian jika sudah ada proses sedang berjalan
    if (isProcessing) {
        requestQueue.push(message);
        messageInput.value = '';
        sendBtn.disabled = true;
        return;
    }
    
    // Set flag proses sedang berjalan
    isProcessing = true;
    
    // Tampilkan pesan pengguna di roomchat
    addMessage(message, true);
    
    // Reset input
    messageInput.value = '';
    sendBtn.disabled = true;
    
    // Tampilkan indikator mengetik
    showTypingIndicator();
    
    try {
        // Kirim pesan ke server dengan timeout
        const response = await Promise.race([
            sendMessage(message),
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Request timeout')), 30000)
            )
        ]);
        
        // Hapus indikator mengetik
        removeTypingIndicator();
        
        if (response && response.response) {
            // Tampilkan respons dari server
            addMessage(response.response, false);
        }
    } catch (error) {
        // Hapus indikator mengetik
        removeTypingIndicator();
        showError(`Kesalahan: ${error.message}`);
    } finally {
        // Reset flag proses
        isProcessing = false;
        
        // Proses antrian berikutnya jika ada
        if (requestQueue.length > 0) {
            messageInput.value = requestQueue.shift();
            setTimeout(handleSendMessage, 500);
        }
    }
}

// Event listener untuk tombol Chat Baru
newChatBtn.addEventListener('click', () => {
    // Buat ID sesi baru
    sessionId = generateSessionId();
    
    // Memuat ulang seluruh halaman
    location.reload();
});

// Event listener untuk pertanyaan yang disarankan
suggestedQuestions.forEach(question => {
    question.addEventListener('click', () => {
        messageInput.value = question.textContent;
        sendBtn.disabled = false;
        handleSendMessage();
    });
});

// Cek status server saat halaman dimuat
checkServerStatus();

// Cek status server setiap 30 detik
setInterval(checkServerStatus, 30000);