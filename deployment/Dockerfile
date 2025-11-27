FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        nginx \
        supervisor \
        openssl && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /usr/src/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your project files
COPY . .

# Copy configs for nginx + supervisor
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisor.conf /etc/supervisor.conf

COPY generate_ssl.sh . 
RUN chmod +x generate_ssl.sh

# Ensure script is executable
RUN chmod +x set_api_key.sh

# Expose ONLY nginx port
EXPOSE 80 443

# Start all services with supervisor
CMD ["/usr/src/app/start_app.sh"]