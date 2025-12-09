#!/data/data/com.termux/files/usr/bin/bash

clear
echo ""
echo "███████╗████████╗"
echo "██╔════╝╚══██╔══╝"
echo "████╗            ██║   "
echo "██╔══╝          ██║   "
echo "██║                ██║   "
echo "╚═╝                ╚═╝   "
echo ""
echo "🔧 Installing CyberStalker v2.0..."
echo ""

# Update packages
pkg update -y && pkg upgrade -y

# Install Python
pkg install python -y
pkg install python-pip -y

# Install dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install instagrapi instaloader phonenumbers cryptography requests

# Create app directory
mkdir -p ~/.cyberstalker
cp ft_osint.py ~/.cyberstalker/
cp requirements.txt ~/.cyberstalker/

# Create launcher script
cat > /data/data/com.termux/files/usr/bin/cyberstalker << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/.cyberstalker
python ft_osint.py
EOF

chmod +x /data/data/com.termux/files/usr/bin/cyberstalker

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 Run: cyberstalker"
echo "📁 Config: ~/.cyberstalker"
echo "📊 Reports: ~/.cyberstalker/Reports"
echo ""
echo "💫 Starting CyberStalker..."
echo ""
sleep 2

cd ~/.cyberstalker
python ft_osint.py