
#!/bin/bash
# Define paths for the generated files
CERT_PATH=/etc/nginx/ssl/
mkdir -p $CERT_PATH

# 1. Define the Common Name (CN)
# Use the value of the HOST_IP environment variable,
# defaulting to 'localhost' if not provided (for local testing).
CN=${HOST_IP:-localhost} 

echo "Generating self-signed SSL certificate with Common Name: ${CN}"

# 2. Generate the certificate using the dynamic CN with subjectAltName
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ${CERT_PATH}nginx.key \
    -out ${CERT_PATH}nginx.crt \
    -subj "/CN=${CN}/O=Docker App/C=US" \
    -addext "subjectAltName=IP:${CN}"
    
echo "SSL certificate generation complete."
echo "Certificate valid for: ${CN}"
echo "Access your app at: https://${CN}"