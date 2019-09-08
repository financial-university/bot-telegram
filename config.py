SQLALCHEMY_DATABASE_URI = f"postgresql://postgres:postgres@localhost:5432/telegram"
token = 'token'

# # Для вебхука
#
# WEBHOOK_HOST = 'localhost'
# WEBHOOK_PORT = 8443  # 443, 80, 88 или 8443
# WEBHOOK_LISTEN = '0.0.0.0'
#
# # SSL certificate generation:
# #
# # openssl genrsa -out webhook_pkey.pem 2048
# # openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
# #
#
# WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
# WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key
#
# WEBHOOK_URL_BASE = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}"
# WEBHOOK_URL_PATH = f"/{token}/"
