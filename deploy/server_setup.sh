#!/bin/bash
# HR-Pro Server Setup Script
# DigitalOcean Ubuntu 22.04/24.04

set -e

echo "=========================================="
echo "  HR-Pro Server Setup"
echo "=========================================="

# 1. System update
echo "[1/8] System yangilanmoqda..."
apt update && apt upgrade -y

# 2. Swap yaratish (1GB RAM uchun muhim)
echo "[2/8] Swap yaratilmoqda (2GB)..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap yaratildi"
else
    echo "Swap allaqachon mavjud"
fi

# 3. Kerakli paketlar
echo "[3/8] Kerakli paketlar o'rnatilmoqda..."
apt install -y \
    python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    nginx \
    git \
    supervisor \
    certbot python3-certbot-nginx \
    ufw

# 4. PostgreSQL sozlash
echo "[4/8] PostgreSQL sozlanmoqda..."
sudo -u postgres psql -c "SELECT 1 FROM pg_roles WHERE rolname='hrpro_user'" | grep -q 1 || {
    sudo -u postgres psql <<EOF
CREATE USER hrpro_user WITH PASSWORD 'HrPro_Secure_2024!';
CREATE DATABASE hrpro_db OWNER hrpro_user;
GRANT ALL PRIVILEGES ON DATABASE hrpro_db TO hrpro_user;
EOF
    echo "PostgreSQL database yaratildi"
}

# 5. App uchun papka
echo "[5/8] App papkasi yaratilmoqda..."
mkdir -p /var/www/hr-pro
mkdir -p /var/log/hr-pro

# 6. Deploy user yaratish
echo "[6/8] Deploy user yaratilmoqda..."
id -u deploy &>/dev/null || {
    useradd -m -s /bin/bash deploy
    usermod -aG sudo deploy
    mkdir -p /home/deploy/.ssh
    cp ~/.ssh/authorized_keys /home/deploy/.ssh/ 2>/dev/null || true
    chown -R deploy:deploy /home/deploy/.ssh
    chown -R deploy:deploy /var/www/hr-pro
    chown -R deploy:deploy /var/log/hr-pro
    echo "deploy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/deploy
}

# 7. Firewall
echo "[7/8] Firewall sozlanmoqda..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# 8. Nginx default config
echo "[8/8] Nginx sozlanmoqda..."
cat > /etc/nginx/sites-available/hr-pro << 'NGINX'
server {
    listen 80;
    server_name _;

    location /static/ {
        alias /var/www/hr-pro/staticfiles/;
    }

    location /media/ {
        alias /var/www/hr-pro/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/hr-pro /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ""
echo "=========================================="
echo "  Server tayyor!"
echo "=========================================="
echo ""
echo "Ma'lumotlar:"
echo "  Database: hrpro_db"
echo "  DB User: hrpro_user"
echo "  DB Password: HrPro_Secure_2024!"
echo "  App path: /var/www/hr-pro"
echo "  Deploy user: deploy"
echo ""
echo "Keyingi qadam: Kodni serverga yuklang"
echo "=========================================="
