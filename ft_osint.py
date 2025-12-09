#!/usr/bin/env python3
# FT - OSINT Tool for Android (Cyberpunk Theme)
# Fixed version with all bugs resolved

import os
import sys
import json
import time
import re
import getpass
import traceback
import subprocess
import phonenumbers
import requests
import base64
import hashlib
import shutil
import contextlib
import io
import instaloader
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor, as_completed
from phonenumbers import carrier, geocoder, timezone, number_type, PhoneNumberFormat

# ========== CONFIGURATION ==========
REPORTS_DIR = Path.cwd() / "Reports"
if not REPORTS_DIR.exists():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOAD_DIR = REPORTS_DIR  # Save everything in Reports folder

# Auto-login config
CONFIG_DIR = Path.home() / ".ft"
CONFIG_FILE = CONFIG_DIR / "auth_config.json"
SESSION_FILE = CONFIG_DIR / "session_data.ft"

# ========== CYBERPUNK COLOR SYSTEM ==========
class Color:
    # Cyberpunk theme colors
    NEON_PINK = '\033[95;1m'
    NEON_BLUE = '\033[94;1m'
    NEON_GREEN = '\033[92;1m'
    NEON_YELLOW = '\033[93;1m'
    NEON_CYAN = '\033[96;1m'
    NEON_PURPLE = '\033[95m'
    NEON_RED = '\033[91;1m'
    MATRIX_GREEN = '\033[92m'
    TERMINAL_BLUE = '\033[94m'
    GLITCH_PURPLE = '\033[35;1m'
    CYBER_ORANGE = '\033[38;5;214m'
    HACKER_GREEN = '\033[38;5;40m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def color_text(text: str, color_code: str, bold: bool = False) -> str:
    color_map = {
        'neon_pink': Color.NEON_PINK, 'neon_blue': Color.NEON_BLUE,
        'neon_green': Color.NEON_GREEN, 'neon_yellow': Color.NEON_YELLOW,
        'neon_cyan': Color.NEON_CYAN, 'neon_purple': Color.NEON_PURPLE,
        'neon_red': Color.NEON_RED, 'matrix': Color.MATRIX_GREEN,
        'terminal': Color.TERMINAL_BLUE, 'glitch': Color.GLITCH_PURPLE,
        'cyber': Color.CYBER_ORANGE, 'hacker': Color.HACKER_GREEN,
        'gold': Color.NEON_YELLOW, 'silver': '\033[90m',
        'teal': Color.NEON_CYAN, 'orange': Color.CYBER_ORANGE,
        'pink': Color.NEON_PINK, 'red': Color.NEON_RED,
        'green': Color.NEON_GREEN, 'blue': Color.NEON_BLUE,
        'cyan': Color.NEON_CYAN, 'magenta': Color.NEON_PURPLE,
        'yellow': Color.NEON_YELLOW
    }
    color = color_map.get(color_code, Color.NEON_CYAN)
    bold_text = Color.BOLD if bold else ""
    return f"{bold_text}{color}{text}{Color.RESET}"

# ========== UTILITY FUNCTIONS ==========
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_separator(char: str = "─", color: str = "neon_cyan", bold: bool = False):
    try:
        width = os.get_terminal_size().columns
    except:
        width = 80
    print(color_text(char * width, color, bold))

def print_header(title: str, color: str = "neon_cyan", emoji: str = "🔍"):
    clear_screen()
    print_separator("━", color, True)
    print(color_text(f"\n  {emoji}  {title}  {emoji}", color, True))
    print_separator("━", color, True)
    print()

def print_status(message: str, status: str = "info", icon: str = ""):
    cyber_icons = {
        "info": "⚡", "success": "✅", "warning": "⚠️", "error": "💥",
        "loading": "🌀", "search": "🔍", "data": "📊", "user": "👤",
        "lock": "🔐", "unlock": "🔓", "star": "✨", "fire": "🔥",
        "rocket": "🚀", "shield": "🛡️", "key": "🔑", "link": "🔗",
        "camera": "📸", "heart": "💗", "money": "💎", "globe": "🌐",
        "clock": "⏱️", "bell": "🔔", "trophy": "🏆", "crown": "👑",
        "gem": "💠", "bolt": "⚡", "flag": "🏴", "phone": "📱",
        "username": "👤", "download": "💾", "hacker": "👨‍💻"
    }

    colors = {
        "info": "neon_cyan", "success": "neon_green", "warning": "neon_yellow",
        "error": "neon_red", "loading": "neon_blue"
    }

    status_icon = icon if icon else cyber_icons.get(status, "⚡")
    color = colors.get(status, "neon_cyan")
    print(f"  {status_icon} {color_text(message, color)}")

def loading_animation(message: str = "Processing", duration: float = 1.0, dots: int = 3):
    cyber_frames = ['⣾','⣽','⣻','⢿','⡿','⣟','⣯','⣷']
    start_time = time.time()
    i = 0
    while time.time() - start_time < duration:
        frame = cyber_frames[i % len(cyber_frames)]
        dots_text = "." * ((i % dots) + 1)
        print(f"\r  {frame} {color_text(message, 'neon_blue')}{dots_text}", end="", flush=True)
        time.sleep(0.08)
        i += 1
    print(f"\r  {color_text('✓', 'neon_green')} {message} complete")

def run_command(cmd: str, timeout: int = 120) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True,
                               text=True, timeout=timeout, encoding='utf-8', errors='ignore')
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -2, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def suppress_instagram_noise(func, *args, **kwargs):
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            result = func(*args, **kwargs)
        return result, ""
    except Exception as e:
        error_msg = str(e)
        if error_msg and len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        return None, error_msg

# ========== ENCRYPTION FUNCTIONS ==========
def init_config():
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        key_file = CONFIG_DIR / ".encryption_key"
        if not key_file.exists():
            key = Fernet.generate_key()
            key_file.write_bytes(key)
        return True
    except Exception as e:
        print_status(f"Config init error: {str(e)}", "error")
        return False

def get_encryption_key():
    try:
        key_file = CONFIG_DIR / ".encryption_key"
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            return key
    except:
        return base64.urlsafe_b64encode(hashlib.sha256(b"ft_backup_key").digest())

def encrypt_data(data: str) -> str:
    try:
        key = get_encryption_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except:
        return base64.urlsafe_b64encode(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    try:
        key = get_encryption_key()
        cipher = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = cipher.decrypt(decoded)
        return decrypted.decode()
    except:
        try:
            return base64.urlsafe_b64decode(encrypted_data.encode()).decode()
        except:
            return ""

def save_credentials(username: str, password: str, toutatis_session: str = ""):
    try:
        if not init_config():
            return False

        config_data = {
            'username': encrypt_data(username),
            'password': encrypt_data(password),
            'toutatis_session': encrypt_data(toutatis_session),
            'last_login': datetime.now().isoformat(),
            'version': '2.0'
        }

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)

        save_instagram_session(username)

        print_status("Credentials saved locally (encrypted)", "success")
        return True
    except Exception as e:
        print_status(f"Save error: {str(e)}", "warning")
        return False

def load_credentials():
    try:
        if not CONFIG_FILE.exists():
            return None, None, None

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        username = decrypt_data(config_data.get('username', ''))
        password = decrypt_data(config_data.get('password', ''))
        toutatis_session = decrypt_data(config_data.get('toutatis_session', ''))

        if username and password:
            print_status("Loaded saved credentials", "success")
            return username, password, toutatis_session
        else:
            return None, None, None
    except Exception as e:
        print_status(f"Load error: {str(e)}", "warning")
        return None, None, None

def clear_credentials():
    try:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
        print_status("Credentials cleared", "success")
        return True
    except:
        return False

def save_instagram_session(username: str):
    try:
        session_file = f"ig_session_{username}.json"
        if os.path.exists(session_file):
            shutil.copy2(session_file, str(SESSION_FILE))
    except:
        pass

def load_instagram_session(username: str):
    try:
        if SESSION_FILE.exists():
            session_file = f"ig_session_{username}.json"
            shutil.copy2(str(SESSION_FILE), session_file)
            return True
    except:
        pass
    return False

def check_auto_login():
    try:
        if not CONFIG_FILE.exists():
            return False

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        last_login = config_data.get('last_login', '')
        if last_login:
            last_date = datetime.fromisoformat(last_login)
            days_diff = (datetime.now() - last_date).days
            if days_diff <= 30:
                return True
        return False
    except:
        return False

# ========== PROFILE PICTURE DOWNLOAD ==========
def download_profile_picture(profile_pic_url: str, username: str) -> str:
    """Download profile picture and return saved path"""
    if not profile_pic_url or profile_pic_url == 'N/A':
        return ""
    
    print_status("Downloading profile picture...", "loading", "📸")
    
    try:
        response = requests.get(profile_pic_url, timeout=10)
        if response.status_code == 200:
            # Detect file extension
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'png' in content_type:
                ext = 'png'
            elif 'webp' in content_type:
                ext = 'webp'
            else:
                if profile_pic_url.lower().endswith(('.jpg', '.jpeg')):
                    ext = 'jpg'
                elif profile_pic_url.lower().endswith('.png'):
                    ext = 'png'
                elif profile_pic_url.lower().endswith('.webp'):
                    ext = 'webp'
                else:
                    ext = 'jpg'
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"FT_{username}_profile_{timestamp}.{ext}"
            filepath = REPORTS_DIR / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print_status(f"Profile picture saved: {filename}", "success", "💾")
            return str(filepath)
        else:
            print_status(f"Failed to download: HTTP {response.status_code}", "error", "💥")
            return ""
    except Exception as e:
        print_status(f"Download error: {str(e)}", "error", "💥")
        return ""

# ========== HTML REPORT GENERATOR ==========
def generate_html_report(data: Dict, target: str, profile_pic_path: str = "") -> str:
    """Generate a beautiful HTML report with cyberpunk theme"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_id = f"FT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Prepare data for HTML
    username = data.get('username', target)
    full_name = data.get('full_name', 'N/A')
    user_id = data.get('user_id', 'N/A')
    is_private = data.get('is_private', False)
    is_verified = data.get('is_verified', False)
    is_business = data.get('is_business', False)
    followers = data.get('follower_count', 'N/A')
    following = data.get('following_count', 'N/A')
    posts = data.get('media_count', 'N/A')
    bio = data.get('biography', 'N/A')
    category = data.get('category', 'N/A')
    email = data.get('email', 'N/A')
    phone = data.get('phone', 'N/A')
    joined_date = data.get('joined_date', 'N/A')
    account_age = data.get('account_age', 'N/A')
    
    # Format numbers
    if followers != 'N/A':
        try:
            followers = f"{int(followers):,}"
        except:
            pass
    if following != 'N/A':
        try:
            following = f"{int(following):,}"
        except:
            pass
    if posts != 'N/A':
        try:
            posts = f"{int(posts):,}"
        except:
            pass
    
    # HTML template with cyberpunk theme - FIXED PROFILE PICTURE
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FT OSINT Report - @{username}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
            color: #00ffff;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(10, 15, 30, 0.9);
            border: 2px solid #00ffff;
            border-radius: 15px;
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.3),
                        0 0 60px rgba(148, 0, 211, 0.2);
            padding: 30px;
            position: relative;
            overflow: hidden;
        }}
        
        .container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #ff0080, #00ffff, #ff0080);
            animation: scanline 3s linear infinite;
        }}
        
        @keyframes scanline {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #ff0080;
            position: relative;
        }}
        
        .header h1 {{
            font-size: 2.8em;
            background: linear-gradient(90deg, #00ffff, #ff0080);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
            margin-bottom: 10px;
            letter-spacing: 2px;
        }}
        
        .header h2 {{
            color: #ff0080;
            font-size: 1.8em;
            margin-bottom: 15px;
        }}
        
        .header .meta {{
            color: #888;
            font-size: 0.9em;
        }}
        
        .profile-section {{
            display: flex;
            flex-wrap: wrap;
            gap: 30px;
            margin-bottom: 40px;
            padding: 25px;
            background: rgba(20, 25, 45, 0.7);
            border-radius: 12px;
            border: 1px solid #333;
        }}
        
        .profile-pic {{
            flex: 0 0 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .profile-pic img {{
            width: 200px;
            height: 200px;
            object-fit: cover;
            border-radius: 10px;
            border: 3px solid #00ffff;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
        }}
        
        .profile-info {{
            flex: 1;
            min-width: 300px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: rgba(25, 30, 50, 0.8);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid #333;
            transition: transform 0.3s, box-shadow 0.3s;
            position: relative;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 255, 255, 0.2);
        }}
        
        .card h3 {{
            color: #ff0080;
            margin-bottom: 20px;
            font-size: 1.4em;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        
        .card .icon {{
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 1.5em;
        }}
        
        .info-item {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px dashed #333;
        }}
        
        .info-item:last-child {{
            border-bottom: none;
            margin-bottom: 0;
        }}
        
        .label {{
            color: #00ffff;
            font-weight: bold;
            display: block;
            margin-bottom: 5px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .value {{
            color: #fff;
            font-size: 1.1em;
            word-break: break-word;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin: 5px 5px 5px 0;
        }}
        
        .badge.private {{ background: #ff4757; color: white; }}
        .badge.verified {{ background: #00b894; color: white; }}
        .badge.business {{ background: #0984e3; color: white; }}
        .badge.public {{ background: #00cec9; color: white; }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .stat {{
            text-align: center;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            border: 1px solid #333;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #00ffff;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #888;
            font-size: 0.9em;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #333;
            color: #888;
            font-size: 0.9em;
        }}
        
        .warning {{
            background: rgba(255, 71, 87, 0.1);
            border-left: 4px solid #ff4757;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            color: #ff6b81;
        }}
        
        .success {{
            background: rgba(0, 184, 148, 0.1);
            border-left: 4px solid #00b894;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            color: #00b894;
        }}
        
        .data-source {{
            font-size: 0.8em;
            color: #888;
            margin-top: 5px;
            font-style: italic;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .profile-section {{
                flex-direction: column;
                align-items: center;
            }}
            
            .profile-pic {{
                width: 100%;
                flex: none;
            }}
            
            .profile-pic img {{
                width: 200px;
                height: 200px;
            }}
        }}
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-search"></i> FT OSINT REPORT</h1>
            <h2>@{username}</h2>
            <div class="meta">
                Report ID: {report_id} | Generated: {timestamp}
            </div>
        </div>
        
        <div class="profile-section">
            <div class="profile-pic">
                {"<img src='" + profile_pic_path.split('/')[-1] + "' alt='Profile Picture' style='width:200px;height:200px;'>" if profile_pic_path else "<div style='width:200px;height:200px;background:#222;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#666;border:3px solid #00ffff;'>No Image Available</div>"}
            </div>
            <div class="profile-info">
                <h3 style="color:#00ffff;margin-bottom:15px;">Target Information</h3>
                <div class="info-item">
                    <span class="label">Full Name</span>
                    <span class="value">{full_name}</span>
                </div>
                <div class="info-item">
                    <span class="label">User ID</span>
                    <span class="value">{user_id}</span>
                </div>
                <div class="info-item">
                    <span class="label">Account Status</span>
                    <span class="value">
                        {"<span class='badge private'><i class='fas fa-lock'></i> PRIVATE</span>" if is_private else "<span class='badge public'><i class='fas fa-globe'></i> PUBLIC</span>"}
                        {"<span class='badge verified'><i class='fas fa-check-circle'></i> VERIFIED</span>" if is_verified else ""}
                        {"<span class='badge business'><i class='fas fa-briefcase'></i> BUSINESS</span>" if is_business else ""}
                    </span>
                </div>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{followers}</div>
                        <div class="stat-label">Followers</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{following}</div>
                        <div class="stat-label">Following</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{posts}</div>
                        <div class="stat-label">Posts</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="info-grid">
            <div class="card">
                <div class="icon">📝</div>
                <h3>Bio & Details</h3>
                <div class="info-item">
                    <span class="label">Biography</span>
                    <span class="value">{bio if len(str(bio)) < 200 else str(bio)[:200] + '...'}</span>
                </div>
                <div class="info-item">
                    <span class="label">Category</span>
                    <span class="value">{category}</span>
                </div>
                <div class="info-item">
                    <span class="label">Account Age</span>
                    <span class="value">{account_age}</span>
                </div>
                <div class="info-item">
                    <span class="label">Joined Date</span>
                    <span class="value">{joined_date}</span>
                </div>
            </div>
            
            <div class="card">
                <div class="icon">📞</div>
                <h3>Contact Information</h3>
                <div class="info-item">
                    <span class="label">Email Address</span>
                    <span class="value">{email if email != 'N/A' else '<span style="color:#888">Not Found</span>'}</span>
                    {"<div class='data-source'>Source: " + data.get('email_source', 'Unknown') + "</div>" if email != 'N/A' else ""}
                </div>
                <div class="info-item">
                    <span class="label">Phone Number</span>
                    <span class="value">{phone if phone != 'N/A' else '<span style="color:#888">Not Found</span>'}</span>
                    {"<div class='data-source'>Source: " + data.get('phone_source', 'Unknown') + "</div>" if phone != 'N/A' else ""}
                </div>
                {"<div class='warning'><i class='fas fa-exclamation-triangle'></i> Note: Phone number is shown exactly as provided by Toutatis</div>" if phone != 'N/A' and 'Toutatis' in data.get('phone_source', '') else ""}
            </div>
            
            <div class="card">
                <div class="icon">🔍</div>
                <h3>Analysis Details</h3>
                <div class="info-item">
                    <span class="label">Data Quality</span>
                    <span class="value">{data.get('data_quality', 'N/A')}</span>
                </div>
                <div class="info-item">
                    <span class="label">Completeness</span>
                    <span class="value">{data.get('data_completeness', 'N/A')}</span>
                </div>
                <div class="info-item">
                    <span class="label">Sources Used</span>
                    <span class="value">
                        {"<span style='color:#00b894'>Instagram</span>" if data.get('sources_used', {}).get('instagram') else ""}
                        {"<span style='color:#0984e3'>Toutatis</span>" if data.get('sources_used', {}).get('toutatis') else ""}
                        {"<span style='color:#a29bfe'>Instaloader</span>" if data.get('sources_used', {}).get('instaloader') else ""}
                    </span>
                </div>
            </div>
        </div>
        
        {"<div class='warning'><i class='fas fa-exclamation-triangle'></i> This is a private account. Limited information available.</div>" if is_private else ""}
        
        <div class="footer">
            <p><i class="fas fa-code"></i> Generated by FT OSINT Tool v2.0</p>
            <p style="font-size:0.8em;margin-top:10px;color:#666;">
                <i class="fas fa-shield-alt"></i> For educational and security research purposes only
            </p>
        </div>
    </div>
    
    <script>
        // Add some cyberpunk effects
        document.addEventListener('DOMContentLoaded', function() {{
            // Pulsing effect for cards
            const cards = document.querySelectorAll('.card');
            cards.forEach(card => {{
                card.addEventListener('mouseenter', () => {{
                    card.style.borderColor = '#00ffff';
                }});
                card.addEventListener('mouseleave', () => {{
                    card.style.borderColor = '#333';
                }});
            }});
            
            // Typewriter effect for header
            const header = document.querySelector('.header h2');
            const text = header.textContent;
            header.textContent = '';
            let i = 0;
            function typeWriter() {{
                if (i < text.length) {{
                    header.textContent += text.charAt(i);
                    i++;
                    setTimeout(typeWriter, 50);
                }}
            }}
            setTimeout(typeWriter, 1000);
        }});
    </script>
</body>
</html>"""
    
    # Save HTML file
    filename = f"FT_Report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = REPORTS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return str(filepath)

# ========== TOUTATIS INTEGRATION ==========
def run_toutatis_locally(target_username: str):
    """Run Toutatis with saved session ID and target username"""
    print_header("TOUTATIS DATA COLLECTION", "neon_purple", "⚡")

    # Try to load saved Toutatis session ID
    saved_user, _, saved_toutatis_session = load_credentials()
    session_id = ""
    
    if saved_toutatis_session and saved_toutatis_session.strip():
        print_status(f"Found saved Toutatis session ID", "success", "🔑")
        use_saved = input(color_text(f"Use saved session ID? (y/n): ", "neon_cyan")).strip().lower()
        if use_saved == 'y':
            session_id = saved_toutatis_session
            print_status("Using saved session ID", "success", "✅")
    
    if not session_id:
        while True:
            print_status("Enter Toutatis session id:", "info", "🔑")
            print(color_text("  • Find in Instagram app: Settings → Security → Access Data → Session ID", "neon_cyan"))
            print(color_text("  • Or use browser developer tools", "neon_cyan"))
            
            session_id = input(color_text("\n📝 Enter session id (or 'skip' to bypass): ", "neon_cyan")).strip()
            
            if session_id.lower() == 'skip':
                print_status("Skipping Toutatis", "warning", "⚠️")
                return {}
            
            if not session_id:
                print_status("Session id is required", "error", "💥")
                continue
                
            if len(session_id) < 10:
                print_status("Session id seems too short", "warning", "⚠️")
                confirm = input(color_text("Use anyway? (y/n): ", "neon_yellow")).strip().lower()
                if confirm != 'y':
                    continue
            
            break

    print_status(f"Running Toutatis for @{target_username}...", "loading", "🌀")
    
    toutatis_cmds = []
    if shutil.which("toutatis"):
        toutatis_cmds.append(f"toutatis -s \"{session_id}\" -u \"{target_username}\"")
    toutatis_cmds.append(f"python -m toutatis -s \"{session_id}\" -u \"{target_username}\"")
    toutatis_cmds.append(f"python3 -m toutatis -s \"{session_id}\" -u \"{target_username}\"")

    success = False
    output = ""
    
    for cmd in toutatis_cmds:
        print_status(f"Trying: {cmd.split()[0]}", "loading", "⚡")
        code, out, err = run_command(cmd, timeout=60)
        output = (out or "") + ("\n" + err if err else "")
        
        if code == 0 and output.strip():
            low_out = output.lower()
            if "invalid session" in low_out or "invalid season" in low_out:
                print_status("Invalid session/season id reported by Toutatis", "error", "💥")
                print(color_text(f"Output preview: {output[:200]}...", "neon_yellow"))
                retry = input(color_text("Try another session id? (y/n): ", "neon_cyan")).strip().lower()
                if retry == 'y':
                    # Clear saved session if it failed
                    if saved_toutatis_session == session_id:
                        save_credentials(saved_user, "", "")  # Clear saved session
                    return run_toutatis_locally(target_username)
                else:
                    return {}
            
            success = True
            print_status("Toutatis executed successfully!", "success", "✅")
            
            # Save the session ID if it worked
            if saved_user:
                save_credentials(saved_user, "", session_id)
            break
        else:
            print_status(f"Command failed (code: {code})", "warning", "⚠️")

    if not success:
        print_status("Auto-run failed. Manual paste mode activated.", "warning", "📝")
        print(color_text("Paste Toutatis output below (type END on a new line when done):", "neon_cyan"))
        print_separator("─", "neon_cyan")

        toutatis_output_lines = []
        try:
            while True:
                try:
                    line = input()
                    if line.strip().upper() == "END":
                        break
                    toutatis_output_lines.append(line)
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
        except:
            pass

        output = "\n".join(toutatis_output_lines)
        if not output.strip():
            print_status("No Toutatis output provided", "warning", "⚠️")
            return {}

    return parse_toutatis_output_comprehensive(output, target_username)

def parse_toutatis_output_comprehensive(text: str, target_username: str) -> Dict:
    """Parse Toutatis output and extract ALL information including obfuscated phone"""
    print_status("Parsing Toutatis data...", "loading", "🔍")
    data = {}
    
    # Store the original output for debugging
    data['raw_toutatis_output'] = text[:5000]  # Store first 5000 chars for reference

    # Remove ANSI codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text = ansi_escape.sub('', text)

    # First, try to find all key-value pairs in the format "key : value"
    lines = clean_text.split('\n')
    
    # Common patterns found in Toutatis output
    patterns = {
        'username': [r'Username[:\s]+@?([A-Za-z0-9_.\-]+)', r'Informations about[:\s]+@?([A-Za-z0-9_.\-]+)'],
        'user_id': [r'userID[:\s]+(\d+)', r'User ID[:\s]+(\d+)', r'ID[:\s]+(\d+)'],
        'full_name': [r'Full Name[:\s]+(.+)'],
        'follower_count': [r'Follower[:\s]+([\d,]+)', r'Followers[:\s]+([\d,]+)'],
        'following_count': [r'Following[:\s]+([\d,]+)'],
        'media_count': [r'Number of posts[:\s]+(\d+)', r'Posts[:\s]+(\d+)'],
        'igtv_posts': [r'IGTV posts[:\s]+(\d+)'],
        'biography': [r'Biography[:\s]+(.+)'],
        'is_verified': [r'Verified[:\s]+(True|False)'],
        'is_business': [r'Is buisness Account[:\s]+(True|False)', r'Business Account[:\s]+(True|False)'],
        'is_private': [r'Is private Account[:\s]+(True|False)', r'Private[:\s]+(True|False)'],
        'linked_whatsapp': [r'Linked WhatsApp[:\s]+(True|False)'],
        'memorial_account': [r'Memorial Account[:\s]+(True|False)'],
        'new_user': [r'New Instagram user[:\s]+(True|False)'],
        # FIXED: Phone number patterns - look for "Obfuscated phone" or "phone"
        'phone': [r'Obfuscated phone[:\s]+(.+)', r'Phone[:\s]+(.+)', r'phone[:\s]+(.+)'],
        'email': [r'Email[:\s]+(.+)'],
        'profile_pic_url': [r'Profile Pic URL[:\s]+(.+)', r'profile_pic_url[:\s]+(.+)']
    }

    # Try each pattern
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and value.lower() not in ['none', 'null', 'na', 'n/a', '']:
                    # Convert boolean strings
                    if field in ['is_verified', 'is_business', 'is_private', 'linked_whatsapp', 'memorial_account', 'new_user']:
                        data[field] = value.lower() in ['true', 'yes', '1']
                    elif field == 'phone':
                        # Store phone exactly as Toutatis gives it
                        data['phone'] = value
                        data['phone_source'] = 'Toutatis'
                        print_status(f"Found phone: {value}", "info", "📱")
                    elif field == 'follower_count' or field == 'following_count':
                        # Remove commas from numbers
                        data[field] = value.replace(',', '')
                    else:
                        data[field] = value
                    break

    # Also parse line by line for key: value format
    for line in lines:
        line = line.strip()
        if ':' in line and len(line.split(':')) >= 2:
            try:
                key_part, value_part = line.split(':', 1)
                key = key_part.strip().lower()
                value = value_part.strip()
                
                if not value or value.lower() in ['none', 'null', 'na', 'n/a', '']:
                    continue
                
                # Map common keys
                if 'user' in key and 'id' in key and 'user_id' not in data:
                    data['user_id'] = value
                elif 'full' in key and 'name' in key and 'full_name' not in data:
                    data['full_name'] = value
                elif 'follower' in key and 'follower_count' not in data:
                    data['follower_count'] = value.replace(',', '')
                elif 'following' in key and 'following_count' not in data:
                    data['following_count'] = value.replace(',', '')
                elif ('post' in key or 'media' in key) and 'media_count' not in data:
                    data['media_count'] = value
                elif 'verified' in key and 'is_verified' not in data:
                    data['is_verified'] = value.lower() in ['true', 'yes', '1']
                elif ('business' in key or 'buisness' in key) and 'is_business' not in data:
                    data['is_business'] = value.lower() in ['true', 'yes', '1']
                elif 'private' in key and 'is_private' not in data:
                    data['is_private'] = value.lower() in ['true', 'yes', '1']
                elif ('obfuscated' in key and 'phone' in key) or ('phone' in key and 'obfuscated' not in key):
                    if 'phone' not in data and value:
                        data['phone'] = value
                        data['phone_source'] = 'Toutatis'
                elif 'bio' in key and 'biography' not in data:
                    data['biography'] = value
            except:
                continue

    # If username not found, use the target
    if 'username' not in data or not data['username']:
        data['username'] = target_username

    # Print all found data
    print_status(f"Parsed {len(data)} fields from Toutatis", "success", "✅")
    
    # Display all Toutatis information
    print()
    print(color_text("📋 TOUTATIS RAW DATA:", "neon_purple", True))
    print_separator("━", "neon_cyan")
    
    # Display key information
    display_fields = [
        ('👤 Username', 'username'),
        ('🆔 User ID', 'user_id'),
        ('📛 Full Name', 'full_name'),
        ('✅ Verified', 'is_verified'),
        ('🏢 Business Account', 'is_business'),
        ('🔒 Private Account', 'is_private'),
        ('👥 Followers', 'follower_count'),
        ('↔️ Following', 'following_count'),
        ('📸 Posts', 'media_count'),
        ('📺 IGTV Posts', 'igtv_posts'),
        ('📞 Phone', 'phone'),
        ('📧 Email', 'email'),
        ('💬 Biography', 'biography'),
        ('📱 Linked WhatsApp', 'linked_whatsapp'),
        ('⚰️ Memorial Account', 'memorial_account'),
        ('🆕 New User', 'new_user')
    ]
    
    for label, field in display_fields:
        if field in data:
            value = data[field]
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            print(f"  {label}: {color_text(str(value), 'neon_cyan')}")
    
    print_separator("━", "neon_cyan")
    
    return data

# ========== INSTALOADER INTEGRATION ==========
def login_instaloader():
    """Login with instaloader"""
    print_status("Attempting Instaloader login...", "loading", "🔐")
    
    L = instaloader.Instaloader()
    
    # Try saved credentials first
    saved_user, saved_pass, _ = load_credentials()
    
    if saved_user and saved_pass:
        try:
            session_file = f"session-{saved_user}"
            if os.path.exists(session_file):
                L.load_session_from_file(saved_user)
                print_status("Instaloader session loaded", "success", "✅")
                return L
            else:
                L.login(saved_user, saved_pass)
                L.save_session_to_file()
                print_status("Instaloader login successful", "success", "✅")
                return L
        except Exception as e:
            print_status(f"Instaloader login failed: {e}", "warning", "⚠️")
            return None
    
    print_status("No saved credentials for Instaloader", "warning", "⚠️")
    return None

def get_instaloader_data(L, username: str) -> Dict:
    """Get Instagram data using instaloader"""
    print_status(f"Fetching data with Instaloader...", "loading", "📥")
    
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        
        data = {
            'username': profile.username,
            'full_name': profile.full_name,
            'follower_count': profile.followers,
            'following_count': profile.followees,
            'media_count': profile.mediacount,
            'is_private': profile.is_private,
            'is_verified': profile.is_verified,
            'is_business': profile.is_business_account,
            'biography': profile.biography,
            'external_url': profile.external_url if profile.external_url else "N/A",
            'profile_pic_url': profile.get_profile_pic_url(),
            'user_id': str(profile.userid),
            'source': 'Instaloader'
        }
        
        print_status(f"Instaloader data fetched: {profile.mediacount} posts", "success", "✅")
        return data
    except Exception as e:
        print_status(f"Instaloader error: {str(e)}", "error", "💥")
        return {}

# ========== INSTAGRAPHI INTEGRATION ==========
def login_instagram():
    print_header("INSTAGRAM LOGIN", "neon_yellow", "🔐")

    if check_auto_login():
        saved_user, saved_pass, _ = load_credentials()
        if saved_user and saved_pass:
            print_status("Attempting auto-login...", "loading", "🔄")
            client = try_auto_login(saved_user, saved_pass)
            if client:
                print_status(f"Auto-login successful! Welcome back @{saved_user}", "success", "🎉")
                return client, saved_user
            print_status("Auto-login failed", "warning", "⚠️")

    print(color_text("📝 MANUAL LOGIN", "neon_yellow", True))
    username = input(color_text("Instagram username: ", "neon_cyan")).strip()
    if not username:
        print_status("Login skipped.", "warning", "⚠️")
        return None, None

    password = getpass.getpass(color_text("Instagram password: ", "neon_cyan"))
    if not password:
        print_status("Password required.", "error", "💥")
        return None, None

    try:
        from instagrapi import Client

        client = Client()
        
        try:
            import logging
            client.logger.setLevel(logging.ERROR)
        except:
            pass

        session_file = f"ig_session_{username}.json"
        load_instagram_session(username)

        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    client.load_settings(json.load(f))
                print_status("Loaded saved session", "success", "📂")
            except:
                pass

        def test_login():
            try:
                client.get_timeline_feed()
                return True
            except:
                return False

        success, _ = suppress_instagram_noise(test_login)
        if not success:
            print_status("Logging in...", "loading", "🔐")
            success, error = suppress_instagram_noise(client.login, username, password)
            if not success:
                print_status(f"Login failed: {error}", "error", "💥")
                return None, None

        if success:
            save_credentials(username, password, "")
            save_instagram_session(username)

        print_status("Login successful! Credentials saved.", "success", "✅")
        return client, username

    except ImportError:
        print_status("Instagrapi not installed! Run: pip install instagrapi", "error", "💥")
        return None, None
    except Exception as e:
        print_status(f"Login error: {str(e)}", "error", "💥")
        return None, None

def try_auto_login(username: str, password: str):
    try:
        from instagrapi import Client
        client = Client()

        try:
            import logging
            client.logger.setLevel(logging.ERROR)
        except:
            pass

        session_file = f"ig_session_{username}.json"
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    client.load_settings(json.load(f))

                def test_session():
                    try:
                        client.get_timeline_feed()
                        return True
                    except:
                        return False

                success, _ = suppress_instagram_noise(test_session)
                if success:
                    return client
            except:
                pass

        print_status("Session expired, logging in...", "loading", "🔐")
        success, error = suppress_instagram_noise(client.login, username, password)
        if success:
            try:
                client.dump_settings(session_file)
                save_instagram_session(username)
            except:
                pass
            return client

        return None
    except:
        return None

def get_instagram_data(client, username: str) -> Dict:
    """Get comprehensive Instagram user data"""
    print_status(f"Fetching Instagram data for @{username}...", "loading", "📥")

    try:
        user, error = suppress_instagram_noise(client.user_info_by_username, username)
        
        if not user:
            print_status(f"Failed to fetch data: {error}", "error", "💥")
            return {}
        
        is_private = bool(getattr(user, 'is_private', False))
        
        if is_private:
            print_status(f"Account @{username} is PRIVATE.", "warning", "🔒")
            
            data = {
                'username': str(getattr(user, 'username', username)),
                'user_id': str(getattr(user, 'pk', '')),
                'full_name': str(getattr(user, 'full_name', '')),
                'biography': str(getattr(user, 'biography', ''))[:200] if getattr(user, 'biography', '') else '',
                'follower_count': int(getattr(user, 'follower_count', 0)),
                'following_count': int(getattr(user, 'following_count', 0)),
                'media_count': int(getattr(user, 'media_count', 0)),
                'is_private': True,
                'is_verified': bool(getattr(user, 'is_verified', False)),
                'is_business': bool(getattr(user, 'is_business', False)),
                'profile_pic_url': str(getattr(user, 'profile_pic_url_hd', '') or getattr(user, 'profile_pic_url', '')),
                'category': str(getattr(user, 'category', 'N/A')),
                'account_type': 'PRIVATE',
                'source': 'Instagrapi'
            }
            
            return data

        join_date = None
        try:
            timestamp = getattr(user, 'created_at', None)
            if timestamp:
                join_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        except:
            pass

        media_count = getattr(user, 'media_count', 0)

        bio = getattr(user, 'biography', '')
        links = []
        if bio:
            link_pattern = r'(https?://[^\s]+)'
            links = re.findall(link_pattern, bio)

        data = {
            'username': str(getattr(user, 'username', '')),
            'user_id': str(getattr(user, 'pk', '')),
            'full_name': str(getattr(user, 'full_name', '')),
            'biography': bio,
            'follower_count': int(getattr(user, 'follower_count', 0)),
            'following_count': int(getattr(user, 'following_count', 0)),
            'media_count': media_count,
            'total_posts': media_count,
            'is_private': False,
            'is_verified': bool(getattr(user, 'is_verified', False)),
            'is_business': bool(getattr(user, 'is_business', False)),
            'external_url': str(getattr(user, 'external_url', '')),
            'profile_pic_url': str(getattr(user, 'profile_pic_url_hd', '') or getattr(user, 'profile_pic_url', '')),
            'category': str(getattr(user, 'category', '')),
            'city_name': str(getattr(user, 'city_name', '')),
            'public_email': str(getattr(user, 'public_email', '')),
            'whatsapp_number': str(getattr(user, 'whatsapp_number', '')),
            'business_contact_method': str(getattr(user, 'business_contact_method', '')),
            'joined_date': join_date,
            'bio_links': links,
            'account_type': 'PUBLIC',
            'source': 'Instagrapi'
        }

        for key, value in data.items():
            if isinstance(value, str) and not value.strip():
                data[key] = "N/A"
            elif value is None:
                data[key] = "N/A"

        # Store email with source if found
        if data.get('public_email') and data['public_email'] != 'N/A':
            data['email'] = data['public_email']
            data['email_source'] = 'Instagrapi'
        
        # Store phone with source if found
        if data.get('whatsapp_number') and data['whatsapp_number'] != 'N/A':
            data['phone'] = data['whatsapp_number']
            data['phone_source'] = 'Instagrapi'

        print_status(f"Instagram data fetched: {media_count} posts", "success", "✅")
        return data

    except Exception as e:
        error_msg = str(e)
        if "rate limited" in error_msg.lower() or "429" in error_msg:
            print_status("Rate limited by Instagram. Please wait.", "error", "⏳")
        else:
            print_status(f"Error fetching data: {error_msg[:100]}", "error", "💥")
        return {}

# ========== DATA MERGING & UTILS ==========
def detect_emails(data: Dict) -> List[str]:
    emails = []
    email_fields = ['email', 'public_email', 'contact_email']

    for field in email_fields:
        if data.get(field) and data[field] != 'N/A':
            email = str(data[field]).strip()
            if '@' in email and '.' in email and len(email) > 5:
                emails.append(email.lower())

    bio = data.get('biography', '')
    if bio and bio != 'N/A':
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        bio_emails = re.findall(email_pattern, bio, re.IGNORECASE)
        emails.extend([email.lower() for email in bio_emails])

    return list(set(emails))

def detect_links(data: Dict) -> List[str]:
    links = []

    link_fields = ['external_url', 'profile_pic_url']
    for field in link_fields:
        if data.get(field) and data[field] != 'N/A':
            link = str(data[field]).strip()
            if link.startswith(('http://', 'https://')):
                links.append(link)

    bio = data.get('biography', '')
    if bio and bio != 'N/A':
        link_pattern = r'(https?://[^\s]+)'
        bio_links = re.findall(link_pattern, bio)
        links.extend(bio_links)

    if data.get('bio_links'):
        links.extend(data['bio_links'])

    return list(set(links))

def merge_all_data(toutatis_data: Dict, instagram_data: Dict, instaloader_data: Dict) -> Dict:
    merged = {}

    all_fields = {
        'username': ['toutatis', 'instagram', 'instaloader'],
        'user_id': ['toutatis', 'instagram', 'instaloader'],
        'full_name': ['toutatis', 'instagram', 'instaloader'],
        'biography': ['toutatis', 'instagram', 'instaloader'],
        'follower_count': ['toutatis', 'instagram', 'instaloader'],
        'following_count': ['toutatis', 'instagram', 'instaloader'],
        'media_count': ['toutatis', 'instagram', 'instaloader'],
        'is_private': ['toutatis', 'instagram', 'instaloader'],
        'is_verified': ['toutatis', 'instagram', 'instaloader'],
        'is_business': ['toutatis', 'instagram', 'instaloader'],
        'external_url': ['toutatis', 'instagram', 'instaloader'],
        'profile_pic_url': ['toutatis', 'instagram', 'instaloader'],
        'category': ['toutatis', 'instagram', 'instaloader'],
        'city_name': ['toutatis', 'instagram'],
        'email': ['toutatis', 'instagram'],
        'phone': ['toutatis', 'instagram'],
        'joined_date': ['instagram', 'toutatis'],
    }

    # First pass: collect data from all sources
    sources_data = {
        'toutatis': toutatis_data,
        'instagram': instagram_data,
        'instaloader': instaloader_data
    }
    
    # Collect all unique fields
    all_collected_fields = set()
    for source_data in sources_data.values():
        if source_data:
            all_collected_fields.update(source_data.keys())
    
    # For each field, try to get from sources in priority order
    for field in all_collected_fields:
        for source in all_fields.get(field, ['toutatis', 'instagram', 'instaloader']):
            source_data = sources_data.get(source, {})
            if source_data and field in source_data and source_data[field] and source_data[field] != 'N/A':
                merged[field] = source_data[field]
                
                # Track source for important fields
                if field in ['email', 'phone']:
                    source_field = f"{field}_source"
                    if source_field in source_data:
                        merged[source_field] = source_data[source_field]
                    else:
                        merged[source_field] = source.capitalize()
                break

    merged['emails'] = detect_emails(merged)
    merged['links'] = detect_links(merged)

    # Add other Toutatis-specific fields that might be missing
    for field in ['igtv_posts', 'linked_whatsapp', 'memorial_account', 'new_user']:
        if field in toutatis_data and field not in merged:
            merged[field] = toutatis_data[field]

    if merged.get('joined_date') and merged['joined_date'] != 'N/A':
        try:
            join_date = datetime.strptime(merged['joined_date'], '%Y-%m-%d')
            days_old = (datetime.now() - join_date).days
            years = days_old // 365
            months = (days_old % 365) // 30

            if years > 0:
                merged['account_age'] = f"{years} year{'s' if years > 1 else ''}"
                if months > 0:
                    merged['account_age'] += f" {months} month{'s' if months > 1 else ''}"
            else:
                merged['account_age'] = f"{months} month{'s' if months > 1 else ''}"

            if days_old < 30:
                merged['account_status'] = "New Account"
            elif days_old < 180:
                merged['account_status'] = "Recent Account"
            elif days_old < 365:
                merged['account_status'] = "Established Account"
            else:
                merged['account_status'] = "Old Account"
        except:
            pass

    merged['analysis_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    merged['sources_used'] = {
        'instagram': bool(instagram_data),
        'toutatis': bool(toutatis_data),
        'instaloader': bool(instaloader_data)
    }

    filled_fields = sum(1 for v in merged.values() if v and v != 'N/A')
    total_fields = len(merged)
    if total_fields > 0:
        completeness = (filled_fields / total_fields) * 100
        merged['data_completeness'] = f"{completeness:.1f}%"

        if completeness >= 80:
            merged['data_quality'] = "Excellent"
        elif completeness >= 60:
            merged['data_quality'] = "Good"
        elif completeness >= 40:
            merged['data_quality'] = "Fair"
        else:
            merged['data_quality'] = "Poor"
    else:
        merged['data_completeness'] = "0%"
        merged['data_quality'] = "No Data"

    return merged

def print_combined_summary(merged: Dict, target_username: str):
    print_header("📊 COMPREHENSIVE SUMMARY", "neon_purple", "📊")
    print_separator("─", "neon_cyan")

    uname = merged.get('username', target_username)
    full = merged.get('full_name', 'N/A')
    uid = merged.get('user_id', 'N/A')

    print(color_text("👤 BASIC INFORMATION", "neon_cyan", True))
    print_separator("━", "neon_blue")
    print(f"  {color_text('Username:', 'neon_cyan')} {color_text('@' + str(uname), 'neon_yellow', True)}")
    print(f"  {color_text('Full Name:', 'neon_cyan')} {color_text(str(full), 'silver')}")
    print(f"  {color_text('User ID:', 'neon_cyan')} {color_text(str(uid), 'silver')}")

    is_private = merged.get('is_private', False)
    is_verified = merged.get('is_verified', False)
    is_business = merged.get('is_business', False)

    status_emoji = "🔒" if is_private else "🌐"
    status_text = "PRIVATE" if is_private else "PUBLIC"
    status_color = "neon_red" if is_private else "neon_green"

    print(f"  {color_text('Status:', 'neon_cyan')} {status_emoji} {color_text(status_text, status_color, True)}")

    if is_verified:
        print(f"  {color_text('✓ VERIFIED ACCOUNT', 'neon_green', True)}")
    if is_business:
        business_type = merged.get('category', 'Business')
        print(f"  {color_text('🏢 ' + business_type.upper() + ' ACCOUNT', 'neon_blue', True)}")

    if merged.get('account_age'):
        print(f"  {color_text('Account Age:', 'neon_cyan')} {color_text(merged['account_age'], 'cyber')}")
    
    print()

    print(color_text("📈 STATISTICS", "neon_cyan", True))
    print_separator("━", "neon_blue")

    followers = merged.get('follower_count', 'N/A')
    following = merged.get('following_count', 'N/A')
    total_posts = merged.get('total_posts', merged.get('media_count', 'N/A'))
    igtv_posts = merged.get('igtv_posts', 'N/A')

    stats = [
        ('Followers', followers, '👥', 'neon_green'),
        ('Following', following, '↔️', 'neon_blue'),
        ('Posts', total_posts, '📸', 'cyber'),
    ]
    
    if igtv_posts != 'N/A':
        stats.append(('IGTV Posts', igtv_posts, '📺', 'neon_purple'))

    for label, value, emoji, color in stats:
        if value != 'N/A':
            try:
                formatted = f"{int(value):,}" if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()) else str(value)
            except:
                formatted = str(value)
            print(f"  {emoji} {color_text(label + ':', 'neon_cyan')} {color_text(formatted, color)}")
        else:
            print(f"  {emoji} {color_text(label + ':', 'neon_cyan')} {color_text('N/A', 'silver')}")
    
    print()

    print(color_text("📞 CONTACT INFORMATION", "neon_cyan", True))
    print_separator("━", "neon_blue")

    emails = merged.get('emails', [])
    if emails:
        print(f"  📧 {color_text('Emails Found:', 'neon_cyan')} {color_text(str(len(emails)), 'neon_green')}")
        for i, e in enumerate(emails[:3], 1):
            print(f"     {color_text(str(i), 'neon_yellow')}. {color_text(e, 'neon_cyan')}")
        if len(emails) > 3:
            print(f"     ... and {len(emails)-3} more")
    else:
        print(f"  📧 {color_text('No emails found', 'silver')}")

    phone = merged.get('phone', None)
    if phone and phone != 'N/A':
        phone_source = merged.get('phone_source', 'Unknown')
        print(f"  📱 {color_text('Phone:', 'neon_cyan')} {color_text(phone, 'neon_cyan')}")
        print(f"     {color_text(f'Source: {phone_source}', 'silver', True)}")
    else:
        print(f"  📱 {color_text('No phone found', 'silver')}")
    
    print()

    print(color_text("📊 DATA QUALITY", "neon_cyan", True))
    print_separator("━", "neon_blue")
    print(f"  {color_text('Completeness:', 'neon_cyan')} {color_text(merged.get('data_completeness', 'N/A'), 'neon_green')}")
    dq = merged.get('data_quality', 'N/A')
    dq_color = 'neon_green' if dq == 'Excellent' else 'green' if dq == 'Good' else 'cyber' if dq == 'Fair' else 'neon_red'
    print(f"  {color_text('Quality:', 'neon_cyan')} {color_text(dq, dq_color)}")
    
    sources = merged.get('sources_used', {})
    if sources:
        source_text = []
        if sources.get('instagram'):
            source_text.append("Instagram")
        if sources.get('toutatis'):
            source_text.append("Toutatis")
        if sources.get('instaloader'):
            source_text.append("Instaloader")
        if source_text:
            print(f"  {color_text('Sources Used:', 'neon_cyan')} {color_text(', '.join(source_text), 'neon_blue')}")

    print_separator("━", "neon_purple")

# ========== PHONE TRACKER ==========
def phone_track():
    print_header("PHONE TRACKER", "neon_green", "📱")
    try:
        phone = input(color_text("Enter phone number (with country code): ", "neon_cyan")).strip()
        if not phone:
            return
        
        print_status(f"Tracking phone: {phone}", "loading", "🔍")
        
        try:
            parsed = phonenumbers.parse(phone, None)
            
            print_separator("─", "neon_green")
            print(color_text("📌 PHONE INFORMATION", "neon_green", True))
            
            formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
            print(f"  {color_text('Formatted:', 'neon_cyan')} {color_text(formatted, 'neon_yellow')}")
            
            country = phonenumbers.region_code_for_number(parsed)
            print(f"  {color_text('Country Code:', 'neon_cyan')} {color_text(country, 'neon_green')}")
            
            try:
                carrier_name = carrier.name_for_number(parsed, "en")
                if carrier_name:
                    print(f"  {color_text('Carrier:', 'neon_cyan')} {color_text(carrier_name, 'neon_blue')}")
            except:
                pass
            
            try:
                location = geocoder.description_for_number(parsed, "en")
                if location:
                    print(f"  {color_text('Location:', 'neon_cyan')} {color_text(location, 'neon_green')}")
            except:
                pass
            
            try:
                timezones = timezone.time_zones_for_number(parsed)
                if timezones:
                    print(f"  {color_text('Timezone:', 'neon_cyan')} {color_text(', '.join(timezones), 'neon_yellow')}")
            except:
                pass
            
            is_valid = phonenumbers.is_valid_number(parsed)
            valid_text = "Yes" if is_valid else "No"
            valid_color = "neon_green" if is_valid else "neon_red"
            print(f"  {color_text('Valid:', 'neon_cyan')} {color_text(valid_text, valid_color)}")
            
            print_separator("─", "neon_green")
            
        except Exception as e:
            print_status(f"Phone parsing error: {str(e)}", "error", "💥")
            
    except Exception as e:
        print_status(f"Error: {str(e)}", "error", "💥")

# ========== SETTINGS MENU ==========
def settings_menu():
    while True:
        print_header("SETTINGS & CONFIGURATION", "neon_yellow", "⚙️")
        
        print(color_text("🔧 SETTINGS MENU", "neon_yellow", True))
        print_separator("━", "neon_yellow")
        print(f"  {color_text('1', 'neon_yellow', True)}. View saved credentials")
        print(f"  {color_text('2', 'neon_yellow', True)}. Clear saved credentials")
        print(f"  {color_text('3', 'neon_yellow', True)}. View configuration")
        print(f"  {color_text('0', 'neon_yellow', True)}. Back to main menu")
        print_separator("━", "neon_yellow")
        
        choice = input(color_text("\nSelect option: ", "neon_cyan")).strip()
        
        if choice == "1":
            print_header("SAVED CREDENTIALS", "neon_cyan", "🔐")
            username, password, toutatis_session = load_credentials()
            if username:
                print(f"  {color_text('Username:', 'neon_cyan')} {color_text(username, 'neon_yellow')}")
                print(f"  {color_text('Password:', 'neon_cyan')} {color_text('••••••••', 'silver')}")
                if toutatis_session:
                    print(f"  {color_text('Toutatis Session:', 'neon_cyan')} {color_text(toutatis_session[:20] + '...' if len(toutatis_session) > 20 else toutatis_session, 'silver')}")
            else:
                print_status("No saved credentials found", "info", "ℹ️")
            input(color_text("\nPress Enter to continue...", "neon_cyan"))
            
        elif choice == "2":
            print_header("CLEAR CREDENTIALS", "neon_red", "🗑️")
            confirm = input(color_text("Are you sure? This cannot be undone (y/n): ", "neon_red")).strip().lower()
            if confirm == 'y':
                if clear_credentials():
                    print_status("Credentials cleared successfully", "success", "✅")
                else:
                    print_status("Failed to clear credentials", "error", "💥")
            input(color_text("\nPress Enter to continue...", "neon_cyan"))
            
        elif choice == "3":
            print_header("CONFIGURATION", "neon_cyan", "📋")
            print(f"  {color_text('Config Directory:', 'neon_cyan')} {color_text(str(CONFIG_DIR), 'neon_yellow')}")
            print(f"  {color_text('Reports Directory:', 'neon_cyan')} {color_text(str(REPORTS_DIR), 'neon_yellow')}")
            print(f"  {color_text('Reports in folder:', 'neon_cyan')} {color_text(str(len(list(REPORTS_DIR.glob('*.html')))), 'neon_green')} HTML files")
            input(color_text("\nPress Enter to continue...", "neon_cyan"))
            
        elif choice == "0":
            return
            
        else:
            print_status("Invalid choice", "error", "💥")
            time.sleep(1)

# ========== MAIN MENU & FLOW ==========
def print_banner():
    clear_screen()
    # Cyberpunk style banner
    banner = r"""
    ███████╗████████╗
    ██╔════╝╚══██╔══╝
    █████╗     ██║   
    ██╔══╝     ██║   
    ██║        ██║   
    ╚═╝        ╚═╝   
    """
    print(color_text(banner, "neon_cyan", True))
    
    # Cyberpunk style subtitle
    subtitle_lines = [
        "╔═══════════════════════════════════════════════════╗",
        "║         C Y B E R P U N K   O S I N T            ║",
        "║         Advanced Instagram Analysis              ║",
        "╚═══════════════════════════════════════════════════╝"
    ]
    
    for line in subtitle_lines:
        print(color_text(line, "neon_purple"))
    
    print()
    print_separator("━", "neon_cyan")
    print(color_text("  Version 2.0 | Optimized for Android/Termux", "neon_green", True))
    print(color_text("  Reports saved in: " + str(REPORTS_DIR), "neon_blue"))
    print_separator("━", "neon_cyan")
    loading_animation("Initializing FT OSINT System", 0.6)

def main_menu():
    while True:
        clear_screen()
        print_banner()
        print(color_text("🎯 MAIN MENU", "neon_cyan", True))
        print_separator("━", "neon_yellow")
        print(f"  {color_text('1', 'neon_yellow', True)}. Instagram OSINT Analysis")
        print(f"  {color_text('2', 'neon_yellow', True)}. Phone Tracker")
        print(f"  {color_text('3', 'neon_yellow', True)}. Settings & Configuration")
        print(f"  {color_text('0', 'neon_yellow', True)}. Exit")
        print_separator("━", "neon_yellow")

        choice = input(color_text("\nSelect option: ", "neon_cyan")).strip()

        if choice == "1":
            instagram_osint_flow()
        elif choice == "2":
            phone_track()
        elif choice == "3":
            settings_menu()
            continue
        elif choice == "0":
            print_status("Thank you for using FT OSINT!", "success", "👋")
            sys.exit(0)
        else:
            print_status("Invalid choice", "error", "💥")
            time.sleep(1)
            continue

        if choice in ['1', '2']:
            print(f"\n{color_text('─'*30, 'neon_cyan')}")
            cont = input(color_text("  Continue? (Y/n): ", "neon_cyan")).strip().lower()
            if cont == 'n':
                print_status("Returning to main menu...", "info", "↩️")
                time.sleep(1)

def instagram_osint_flow():
    print_header("INSTAGRAM OSINT ANALYSIS", "neon_purple", "📸")

    # Ask for target username only ONCE at the beginning
    while True:
        target = input(color_text("🎯 Target Instagram username (without @): ", "neon_cyan")).strip()
        if target:
            target = target.replace('@', '')
            break
        print_status("Username is required!", "error", "💥")
    
    print_status(f"Target set: @{target}", "success", "🎯")
    
    # Run all three tools with the same target
    print(color_text("\nStep 1: TOUTATIS DATA", "neon_cyan", True))
    print_separator("─", "neon_cyan")
    toutatis_data = run_toutatis_locally(target)
    
    print(color_text("\nStep 2: INSTAGRAPI DATA", "neon_cyan", True))
    print_separator("─", "neon_cyan")
    print_status("Logging in with Instagrapi...", "loading", "🔐")
    client, login_user = login_instagram()
    
    print(color_text("\nStep 3: INSTALOADER DATA", "neon_cyan", True))
    print_separator("─", "neon_cyan")
    print_status("Logging in with Instaloader...", "loading", "🔐")
    L = login_instaloader()

    # Collect data from all three sources using the SAME target
    print_header(f"COLLECTING DATA FOR @{target}", "neon_purple", "🔍")
    
    instagram_data = {}
    instaloader_data = {}
    
    if client and login_user:
        print_status("Fetching data with Instagrapi...", "loading", "📥")
        instagram_data = get_instagram_data(client, target)
    
    if L:
        print_status("Fetching data with Instaloader...", "loading", "📥")
        instaloader_data = get_instaloader_data(L, target)

    loading_animation("Processing and merging data from all sources", 1.0)
    merged_data = merge_all_data(toutatis_data, instagram_data, instaloader_data)
    merged_data['target'] = target

    # Download profile picture
    profile_pic_path = ""
    profile_pic_url = merged_data.get('profile_pic_url')
    if profile_pic_url and profile_pic_url != 'N/A':
        profile_pic_path = download_profile_picture(profile_pic_url, target)

    print_combined_summary(merged_data, target)

    # Generate HTML report
    print()
    save_report = input(color_text("Generate HTML report? (y/n): ", "neon_cyan")).strip().lower()
    if save_report == 'y':
        report_path = generate_html_report(merged_data, target, profile_pic_path)
        if report_path:
            print_status(f"📄 HTML Report generated: {report_path}", "success", "💾")
            print_status(f"📁 All reports saved in: {REPORTS_DIR}", "info", "📂")
            
            # Show report preview
            print()
            print(color_text("🔗 Quick Actions:", "neon_yellow", True))
            print(f"  {color_text('1', 'neon_yellow')}. Open report in browser")
            print(f"  {color_text('2', 'neon_yellow')}. View reports folder")
            print(f"  {color_text('3', 'neon_yellow')}. Continue")
            
            action = input(color_text("\nSelect action: ", "neon_cyan")).strip()
            
            if action == "1":
                try:
                    import webbrowser
                    webbrowser.open(f"file://{report_path}")
                    print_status("Opening report in browser...", "success", "🌐")
                except:
                    print_status("Could not open browser automatically", "warning", "⚠️")
                    print(f"  Manually open: {report_path}")
            elif action == "2":
                print_status(f"Reports folder: {REPORTS_DIR}", "info", "📂")
                print(f"  Total reports: {len(list(REPORTS_DIR.glob('*.html')))} HTML files")
    
    input(color_text("\nPress Enter to return to main menu...", "neon_cyan"))

# ========== MAIN ==========
def main():
    try:
        init_config()
        main_menu()
    except KeyboardInterrupt:
        print(f"\n{color_text('💥 Operation cancelled by user', 'neon_red')}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{color_text(f'💥 Unexpected error: {e}', 'neon_red')}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()