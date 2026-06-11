# Gunicorn configuration for HR-Pro
# /var/www/hr-pro/gunicorn.conf.py

bind = "127.0.0.1:8000"
workers = 2  # 1 vCPU uchun optimal
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/hr-pro/access.log"
errorlog = "/var/log/hr-pro/error.log"
loglevel = "info"

# Process naming
proc_name = "hr-pro"

# Server mechanics
daemon = False
pidfile = "/var/run/hr-pro/gunicorn.pid"
user = "deploy"
group = "deploy"
tmp_upload_dir = None

# Memory management (muhim 1-2GB RAM uchun)
max_requests = 1000
max_requests_jitter = 50
