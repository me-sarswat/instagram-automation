# Deployment Guide

## Local Development

### Prerequisites
- Python 3.8+
- Chrome or Firefox
- Git

### Steps

```bash
# 1. Clone repository
git clone https://github.com/me-sarswat/instagram-automation.git
cd instagram-automation

# 2. Run setup
./setup.sh  # or setup.bat on Windows

# 3. Configure
cp config.example.json config.json
# Edit config.json with your credentials

# 4. Run
source venv/bin/activate
python app.py
```

## Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Steps

```bash
# 1. Clone repository
git clone https://github.com/me-sarswat/instagram-automation.git
cd instagram-automation

# 2. Create .env file
cp .env.example .env
# Edit .env with your credentials

# 3. Start services
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# 5. Stop services
docker-compose down
```

## Heroku Deployment

```bash
# 1. Login to Heroku
heroku login

# 2. Create app
heroku create instagram-automation-app

# 3. Set environment variables
heroku config:set INSTAGRAM_USERNAME=your_username
heroku config:set INSTAGRAM_PASSWORD=your_password
heroku config:set ACCOUNTS_TO_MONITOR=account1,account2

# 4. Add Procfile
echo "web: gunicorn app:app" > Procfile

# 5. Deploy
git push heroku main

# 6. View logs
heroku logs --tail
```

## AWS EC2 Deployment

```bash
# 1. SSH into instance
ssh -i key.pem ubuntu@your-instance-ip

# 2. Install dependencies
sudo apt-get update
sudo apt-get install python3-pip python3-venv git chromium-browser

# 3. Clone and setup
git clone https://github.com/me-sarswat/instagram-automation.git
cd instagram-automation
./setup.sh

# 4. Configure
cp config.example.json config.json
nano config.json

# 5. Create systemd service
sudo nano /etc/systemd/system/instagram-automation.service
```

## Production Considerations

### Security
- [ ] Use HTTPS with reverse proxy (Nginx/Apache)
- [ ] Set strong environment variables
- [ ] Use secrets management (AWS Secrets Manager)
- [ ] Enable 2FA on Instagram account
- [ ] Regular security audits

### Monitoring
- [ ] Set up application monitoring (New Relic, DataDog)
- [ ] Configure error tracking (Sentry)
- [ ] Monitor resource usage
- [ ] Set up alerts for failures

### Backup & Recovery
- [ ] Regular data backups
- [ ] Automated snapshots
- [ ] Disaster recovery plan

### Performance
- [ ] Use caching (Redis)
- [ ] Database optimization
- [ ] Load balancing

## Nginx Reverse Proxy Setup

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Application won't start
```bash
python -m py_compile app.py
python -u app.py
```

### Port already in use
```bash
lsof -i :5000
kill -9 <PID>
```

### Selenium/Chrome issues
```bash
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
apt-get update
apt-get install google-chrome-stable
```