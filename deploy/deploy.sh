#!/bin/bash
# HR-Pro Deployment Script
# Lokal mashinadan serverga deploy qilish

set -e

SERVER="root@137.184.104.67"
APP_PATH="/var/www/hr-pro"

echo "=========================================="
echo "  HR-Pro Deployment"
echo "=========================================="

# 1. Kodni serverga yuklash
echo "[1/5] Kod serverga yuklanmoqda..."
rsync -avz --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'db.sqlite3' \
    --exclude '.env' \
    --exclude 'staticfiles' \
    --exclude 'media' \
    ./ ${SERVER}:${APP_PATH}/

# 2. Virtual environment va dependencies
echo "[2/5] Dependencies o'rnatilmoqda..."
ssh ${SERVER} << 'REMOTE'
cd /var/www/hr-pro
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements/prod.txt
pip install gunicorn psycopg2-binary
REMOTE

# 3. Django setup
echo "[3/5] Django sozlanmoqda..."
ssh ${SERVER} << 'REMOTE'
cd /var/www/hr-pro
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py collectstatic --noinput
python manage.py migrate
REMOTE

# 4. Supervisor config
echo "[4/5] Supervisor sozlanmoqda..."
ssh ${SERVER} << 'REMOTE'
cp /var/www/hr-pro/deploy/supervisor.conf /etc/supervisor/conf.d/hr-pro.conf
mkdir -p /var/run/hr-pro
chown deploy:deploy /var/run/hr-pro
supervisorctl reread
supervisorctl update
supervisorctl restart hr-pro
REMOTE

# 5. Nginx restart
echo "[5/5] Nginx qayta ishga tushirilmoqda..."
ssh ${SERVER} "systemctl restart nginx"

echo ""
echo "=========================================="
echo "  Deploy tugadi!"
echo "=========================================="
echo "  URL: http://137.184.104.67"
echo "=========================================="
