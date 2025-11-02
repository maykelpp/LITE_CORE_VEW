from flask import Flask, render_template_string, request, send_file, jsonify
import yt_dlp
import os
import re
import time
from pathlib import Path
import glob

app = Flask(__name__)

# Directorio para descargas
DOWNLOAD_FOLDER = 'downloads'
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LITE CORE | Plataforma Multi-Uso</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #00D9FF;
            --primary-dark: #00B8D4;
            --secondary: #FF006E;
            --accent: #8338EC;
            --bg-dark: #0A0E27;
            --bg-darker: #050714;
            --surface: #151932;
            --surface-light: #1E2347;
            --text: #FFFFFF;
            --text-muted: #A8B2D1;
            --success: #00F5A0;
            --error: #FF3366;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-darker);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Animated Background */
        .bg-animated {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--bg-darker) 0%, var(--bg-dark) 100%);
            z-index: 0;
        }
        
        .bg-animated::before {
            content: '';
            position: absolute;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
            border-radius: 50%;
            filter: blur(100px);
            opacity: 0.15;
            animation: float1 20s ease-in-out infinite;
            top: -200px;
            right: -200px;
        }
        
        .bg-animated::after {
            content: '';
            position: absolute;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, var(--secondary) 0%, transparent 70%);
            border-radius: 50%;
            filter: blur(120px);
            opacity: 0.1;
            animation: float2 25s ease-in-out infinite;
            bottom: -300px;
            left: -300px;
        }
        
        .grid-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 217, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 217, 255, 0.05) 1px, transparent 1px);
            background-size: 50px 50px;
            z-index: 1;
            pointer-events: none;
        }
        
        .container {
            position: relative;
            z-index: 2;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        /* Header */
        .header {
            padding: 40px 0;
            text-align: center;
            animation: fadeInDown 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .logo-container {
            display: inline-flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            padding: 15px 30px;
            background: rgba(0, 217, 255, 0.1);
            border: 1px solid rgba(0, 217, 255, 0.3);
            border-radius: 50px;
            backdrop-filter: blur(10px);
        }
        
        .logo {
            font-size: 2.5em;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            letter-spacing: -2px;
        }
        
        .version-badge {
            padding: 5px 12px;
            background: var(--primary);
            color: var(--bg-darker);
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 700;
            text-transform: uppercase;
        }
        
        .subtitle {
            font-size: 1.2em;
            color: var(--text-muted);
            font-weight: 400;
        }
        
        /* Main Card */
        .main-card {
            background: rgba(21, 25, 50, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 50px;
            backdrop-filter: blur(20px);
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(255, 255, 255, 0.05) inset;
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            margin-bottom: 30px;
        }
        
        /* Tabs Navigation */
        .tabs-nav {
            display: flex;
            gap: 10px;
            margin-bottom: 40px;
            padding: 8px;
            background: rgba(10, 14, 39, 0.6);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .tab-btn {
            flex: 1;
            padding: 15px 25px;
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1em;
            font-weight: 600;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
        }
        
        .tab-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .tab-btn span {
            position: relative;
            z-index: 1;
        }
        
        .tab-btn:hover {
            color: var(--text);
        }
        
        .tab-btn.active {
            color: var(--text);
            background: linear-gradient(135deg, var(--primary), var(--accent));
        }
        
        .tab-btn.active::before {
            opacity: 1;
        }
        
        /* Tab Content */
        .tab-content {
            display: none;
            animation: fadeIn 0.5s ease;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Input Section */
        .input-group {
            margin-bottom: 30px;
        }
        
        .input-label {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            font-size: 1em;
            font-weight: 600;
            color: var(--text);
        }
        
        .input-label .icon {
            font-size: 1.3em;
        }
        
        .input-wrapper {
            position: relative;
        }
        
        .input-field {
            width: 100%;
            padding: 20px 60px 20px 20px;
            background: rgba(10, 14, 39, 0.6);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            color: var(--text);
            font-size: 16px;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s;
        }
        
        .input-field:focus {
            outline: none;
            border-color: var(--primary);
            background: rgba(10, 14, 39, 0.8);
            box-shadow: 0 0 0 4px rgba(0, 217, 255, 0.1);
        }
        
        .input-field::placeholder {
            color: var(--text-muted);
        }
        
        .clear-btn {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            width: 35px;
            height: 35px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 10px;
            color: var(--text-muted);
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }
        
        .clear-btn:hover {
            background: var(--error);
            color: white;
        }
        
        /* Format Selector */
        .format-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .format-card {
            position: relative;
            padding: 25px 20px;
            background: rgba(10, 14, 39, 0.4);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            overflow: hidden;
        }
        
        .format-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .format-card:hover {
            transform: translateY(-5px);
            border-color: var(--primary);
            box-shadow: 0 10px 30px rgba(0, 217, 255, 0.3);
        }
        
        .format-card.selected {
            border-color: var(--primary);
            background: rgba(0, 217, 255, 0.1);
        }
        
        .format-card.selected::before {
            opacity: 0.15;
        }
        
        .format-card input {
            display: none;
        }
        
        .format-content {
            position: relative;
            z-index: 1;
        }
        
        .format-icon {
            font-size: 2.5em;
            margin-bottom: 10px;
            filter: drop-shadow(0 0 10px currentColor);
        }
        
        .format-title {
            font-weight: 600;
            font-size: 1em;
            margin-bottom: 5px;
        }
        
        .format-desc {
            font-size: 0.8em;
            color: var(--text-muted);
        }
        
        /* Platform Badges */
        .platforms {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 30px;
        }
        
        .platform-badge {
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            color: var(--text-muted);
            transition: all 0.3s;
        }
        
        .platform-badge:hover {
            background: rgba(0, 217, 255, 0.1);
            border-color: var(--primary);
            color: var(--primary);
            transform: translateY(-2px);
        }
        
        /* Action Button */
        .action-btn {
            width: 100%;
            padding: 20px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border: none;
            border-radius: 16px;
            color: white;
            font-size: 1.1em;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
        }
        
        .action-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .action-btn:hover:not(:disabled) {
            transform: translateY(-3px);
            box-shadow: 0 20px 40px rgba(0, 217, 255, 0.4);
        }
        
        .action-btn:active:not(:disabled)::before {
            width: 300px;
            height: 300px;
        }
        
        .action-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .btn-content {
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        
        /* Status Messages */
        .status {
            margin-top: 30px;
            padding: 25px;
            border-radius: 16px;
            display: none;
            animation: slideInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .status.loading {
            background: rgba(0, 217, 255, 0.1);
            border: 1px solid rgba(0, 217, 255, 0.3);
            display: block;
        }
        
        .status.success {
            background: rgba(0, 245, 160, 0.1);
            border: 1px solid rgba(0, 245, 160, 0.3);
            display: block;
        }
        
        .status.error {
            background: rgba(255, 51, 102, 0.1);
            border: 1px solid rgba(255, 51, 102, 0.3);
            display: block;
        }
        
        .status-content {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .status-icon {
            font-size: 2em;
            flex-shrink: 0;
        }
        
        .status-text {
            flex: 1;
        }
        
        .status-text strong {
            display: block;
            margin-bottom: 5px;
            font-size: 1.1em;
        }
        
        .status-text small {
            color: var(--text-muted);
        }
        
        /* Download Link */
        .download-link {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            margin-top: 15px;
            padding: 12px 24px;
            background: var(--success);
            color: var(--bg-darker);
            text-decoration: none;
            border-radius: 12px;
            font-weight: 700;
            transition: all 0.3s;
        }
        
        .download-link:hover {
            background: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 245, 160, 0.3);
        }
        
        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
            display: none;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            border-radius: 10px;
            animation: progress 2s ease-in-out infinite;
        }
        
        /* Spinner */
        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid rgba(255, 255, 255, 0.2);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        /* Features Grid */
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        
        .feature-card {
            padding: 30px;
            background: rgba(10, 14, 39, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            text-align: center;
            transition: all 0.3s;
        }
        
        .feature-card:hover {
            background: rgba(10, 14, 39, 0.6);
            border-color: var(--primary);
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 2.5em;
            margin-bottom: 15px;
            filter: drop-shadow(0 0 10px currentColor);
        }
        
        .feature-title {
            font-size: 1.1em;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .feature-desc {
            font-size: 0.9em;
            color: var(--text-muted);
            line-height: 1.6;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-muted);
            font-size: 0.9em;
        }
        
        /* Animations */
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
        
        @keyframes float1 {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(100px, 100px); }
        }
        
        @keyframes float2 {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(-100px, -100px); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .main-card {
                padding: 30px 20px;
            }
            
            .logo {
                font-size: 2em;
            }
            
            .tabs-nav {
                flex-direction: column;
            }
            
            .format-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="bg-animated"></div>
    <div class="grid-overlay"></div>
    
    <div class="container">
        <header class="header">
            <div class="logo-container">
                <span class="logo">LITE CORE</span>
                <span class="version-badge">WEB VERSION</span>
            </div>
            <p class="subtitle">Plataforma Multi-Uso de Alta Performance</p>
        </header>
        
        <div class="main-card">
            <div class="tabs-nav">
                <button class="tab-btn active" data-tab="downloader">
                    <span>📥 Descargador</span>
                </button>
                <button class="tab-btn" data-tab="converter">
                    <span>🔄 Conversor</span>
                </button>
                <button class="tab-btn" data-tab="tools">
                    <span>🛠️ Herramientas</span>
                </button>
            </div>
            
            <!-- Tab: Descargador -->
            <div class="tab-content active" id="downloader">
                <div class="platforms">
                    <span class="platform-badge">🎵 TikTok</span>
                    <span class="platform-badge">📺 YouTube</span>
                    <span class="platform-badge">📸 Instagram</span>
                    <span class="platform-badge">🐦 Twitter/X</span>
                    <span class="platform-badge">📱 Facebook</span>
                </div>
                
                <form id="downloadForm">
                    <div class="input-group">
                        <label class="input-label">
                            <span class="icon">🔗</span>
                            <span>URL del Contenido</span>
                        </label>
                        <div class="input-wrapper">
                            <input type="text" 
                                   id="url" 
                                   class="input-field" 
                                   placeholder="Pega aquí la URL del video o audio..."
                                   required>
                            <button type="button" class="clear-btn" id="clearBtn">✕</button>
                        </div>
                    </div>
                    
                    <label class="input-label">
                        <span class="icon">⚙️</span>
                        <span>Formato de Salida</span>
                    </label>
                    <div class="format-grid">
                        <label class="format-card selected">
                            <input type="radio" name="format" value="video" checked>
                            <div class="format-content">
                                <div class="format-icon">🎬</div>
                                <div class="format-title">Video HD</div>
                                <div class="format-desc">MP4 Alta Calidad</div>
                            </div>
                        </label>
                        <label class="format-card">
                            <input type="radio" name="format" value="audio">
                            <div class="format-content">
                                <div class="format-icon">🎵</div>
                                <div class="format-title">Audio</div>
                                <div class="format-desc">MP3 192kbps</div>
                            </div>
                        </label>
                        <label class="format-card">
                            <input type="radio" name="format" value="best">
                            <div class="format-content">
                                <div class="format-icon">⭐</div>
                                <div class="format-title">Máxima</div>
                                <div class="format-desc">Mejor Calidad</div>
                            </div>
                        </label>
                    </div>
                    
                    <button type="submit" class="action-btn" id="downloadBtn">
                        <div class="btn-content">
                            <span id="btnText">⚡ Descargar Ahora</span>
                        </div>
                    </button>
                    
                    <div class="progress-bar" id="progressBar">
                        <div class="progress-fill"></div>
                    </div>
                </form>
                
                <div id="status" class="status"></div>
            </div>
            
            <!-- Tab: Conversor -->
            <div class="tab-content" id="converter">
                <div style="text-align: center; padding: 60px 20px;">
                    <div style="font-size: 4em; margin-bottom: 20px;">🔄</div>
                    <h2 style="margin-bottom: 15px;">Conversor de Medios</h2>
                    <p style="color: var(--text-muted); font-size: 1.1em;">Próximamente: Convierte videos y audio entre múltiples formatos</p>
                </div>
            </div>
            
            <!-- Tab: Herramientas -->
            <div class="tab-content" id="tools">
                <div style="text-align: center; padding: 60px 20px;">
                    <div style="font-size: 4em; margin-bottom: 20px;">🛠️</div>
                    <h2 style="margin-bottom: 15px;">Suite de Herramientas</h2>
                    <p style="color: var(--text-muted); font-size: 1.1em;">Próximamente: Edición, compresión y más utilidades</p>
                </div>
            </div>
            
            <div class="features">
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-title">Ultra Rápido</div>
                    <div class="feature-desc">Procesamiento de alta velocidad con tecnología optimizada</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔒</div>
                    <div class="feature-title">Seguro</div>
                    <div class="feature-desc">Tus datos están protegidos con encriptación avanzada</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🌐</div>
                    <div class="feature-title">Multi-Plataforma</div>
                    <div class="feature-desc">Compatible con todas las principales redes sociales</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-title">Sin Límites</div>
                    <div class="feature-desc">Descarga todo el contenido que necesites sin restricciones</div>
                </div>
            </div>
        </div>
        
        <footer class="footer">
            <p>LITE CORE Web Version | Plataforma Multi-Uso de Alta Performance</p>
            <p style="margin-top: 10px; opacity: 0.7;">Powered by Advanced Technology Stack</p>
        </footer>
    </div>

    <script>
        // Tab Switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                btn.classList.add('active');
                document.getElementById(tabName).classList.add('active');
            });
        });
        
        // Form Elements
        const form = document.getElementById('downloadForm');
        const statusDiv = document.getElementById('status');
        const downloadBtn = document.getElementById('downloadBtn');
        const btnText = document.getElementById('btnText');
        const urlInput = document.getElementById('url');
        const clearBtn = document.getElementById('clearBtn');
        const progressBar = document.getElementById('progressBar');
        
        // Clear Button
        urlInput.addEventListener('input', () => {
            clearBtn.style.display = urlInput.value ? 'flex' : 'none';
        });
        
        clearBtn.addEventListener('click', () => {
            urlInput.value = '';
            clearBtn.style.display = 'none';
            urlInput.focus();
        });
        
        // Format Selection
        document.querySelectorAll('.format-card').forEach(card => {
            card.addEventListener('click', () => {
                document.querySelectorAll('.format-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                card.querySelector('input').checked = true;
            });
        });
        
        // Form Submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = urlInput.value.trim();
            const format = document.querySelector('input[name="format"]:checked').value;
            
            // Loading State
            statusDiv.className = 'status loading';
            statusDiv.innerHTML = `
                <div
