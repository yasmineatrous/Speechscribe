# Gunicorn configuration file for the application

# Binding
bind = "0.0.0.0:5000"
port = 5000

# Worker processes - use 1 for development
workers = 1

# Timeout in seconds
timeout = 300  # increased timeout for audio file processing (5 minutes)

# Maximum request body size
# 100MB max request size (primarily for audio file uploads)
limit_request_line = 8190
limit_request_field_size = 0  # 0 means unlimited
limit_request_fields = 100

# Logging
loglevel = "debug"
accesslog = "-"  # stdout
errorlog = "-"   # stderr

# Enable auto-reload to detect code changes
reload = True

# Worker class
worker_class = "sync"