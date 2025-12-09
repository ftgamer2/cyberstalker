#!/data/data/com.termux/files/usr/bin/bash

clear
echo ""
echo "███████╗████████╗"
echo "██╔════╝╚══██╔══╝"
echo "████╗      ██║   "
echo "██╔═╝      ██║   "
echo "██║        ██║   "
echo "╚═╝        ╚═╝   "
echo ""
echo "🔧 Installing CyberStalker v2.0..."
echo ""

# Update packages
pkg update -y && pkg upgrade -y

# Install Python
pkg install python -y
pkg install python-pip -y
pkg install toutatis
# Install dependencies
echo "📦 Installing Python packages..."
# Try installing numpy first (this is what's causing the hang)
pkg install python-numpy -y

# Then try instagrapi again
pip install instagrapi --no-deps
pip install PySocks 
pip install instaloader phonenumbers cryptography requests

# fix toutaris issue
sed -i 's/infos\["total_igtv_videos"\]/infos.get("total_igtv_videos", 0)/' \
/data/data/com.termux/files/usr/lib/python3.12/site-packages/toutatis/core.py

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
