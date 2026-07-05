# SmartBI Deployment Guide

This guide covers deploying SmartBI to various platforms including local, Render, Railway, and Docker.

## Prerequisites

- Python 3.10+
- PostgreSQL database (Neon recommended)
- Git
- pip

## 1. Local Deployment (Windows)

### Step 1: Setup Environment

```cmd
# Clone repository
git clone https://github.com/yourusername/smartbi.git
cd smartbi

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Database

1. Create Neon database at https://neon.tech
2. Copy connection string
3. Create `.env` file:

```env
SMARTBI_SECRET_KEY=your-secret-key-change-this
SMARTBI_DATABASE_URL=postgresql://user:password@host/smartbi
SMARTBI_ADMIN_USERNAME=admin
SMARTBI_ADMIN_PASSWORD=change-this-password
SMARTBI_UPLOAD_FOLDER=backend/uploads
SMARTBI_CLEANED_FOLDER=backend/cleaned
SMARTBI_PROCESSED_FOLDER=backend/processed
SMARTBI_ORIGINAL_FOLDER=backend/original
SMARTBI_MAX_UPLOAD_BYTES=26214400
```

### Step 3: Initialize Database

```cmd
# Install PostgreSQL client (psql) if not installed
# Download from: https://www.postgresql.org/download/windows/

# Run schema
psql -h your-neon-host -U your-user -d smartbi -f sql/schema.sql

# Run Power BI views
psql -h your-neon-host -U your-user -d smartbi -f sql/powerbi_views.sql
```

Or use a PostgreSQL GUI tool like pgAdmin, DBeaver, or DataGrip.

### Step 4: Run Application

```cmd
python run.py
```

Access at: http://localhost:5000

### Step 5: Create Directories

```cmd
mkdir backend\uploads backend\cleaned backend\processed backend\original
```

## 2. Local Deployment (Linux/Mac)

### Step 1: Setup Environment

```bash
# Clone repository
git clone https://github.com/yourusername/smartbi.git
cd smartbi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Database

Same as Windows - create `.env` file with database credentials.

### Step 3: Initialize Database

```bash
# Install psql if needed
# Ubuntu/Debian: sudo apt install postgresql-client
# Mac: brew install postgresql

# Run schema
psql -h your-neon-host -U your-user -d smartbi -f sql/schema.sql
psql -h your-neon-host -U your-user -d smartbi -f sql/powerbi_views.sql
```

### Step 4: Run Application

```bash
python run.py
```

### Step 5: Create Directories

```bash
mkdir -p backend/uploads backend/cleaned backend/processed backend/original
```

## 3. Render Deployment

### Step 1: Prepare Repository

1. Push code to GitHub
2. Ensure `.gitignore` excludes sensitive files
3. Verify `requirements.txt` is up to date

### Step 2: Create Render Account

1. Sign up at https://render.com
2. Connect GitHub account

### Step 3: Create PostgreSQL Database (Optional)

If not using Neon:
1. Click **New** > **PostgreSQL**
2. Choose free tier or paid
3. Note connection details

### Step 4: Create Web Service

1. Click **New** > **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: smartbi
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -b 0.0.0.0:$PORT run:app`
   - **Instance Type**: Free or Starter

### Step 5: Add Environment Variables

In Render dashboard, add:

```
SMARTBI_SECRET_KEY=your-production-secret-key
SMARTBI_DATABASE_URL=postgresql://user:pass@host/database
SMARTBI_ADMIN_USERNAME=admin
SMARTBI_ADMIN_PASSWORD=secure-production-password
SMARTBI_UPLOAD_FOLDER=/tmp/uploads
SMARTBI_CLEANED_FOLDER=/tmp/cleaned
SMARTBI_PROCESSED_FOLDER=/tmp/processed
SMARTBI_ORIGINAL_FOLDER=/tmp/original
SMARTBI_MAX_UPLOAD_BYTES=26214400
```

**Note**: Render uses ephemeral file systems. Files in `/tmp` are temporary. Consider S3 for persistent storage.

### Step 6: Add gunicorn to requirements

Add to `requirements.txt`:
```
gunicorn==21.2.0
```

### Step 7: Initialize Database

Run SQL files using Render's PostgreSQL dashboard or via psql:

```bash
psql $DATABASE_URL -f sql/schema.sql
psql $DATABASE_URL -f sql/powerbi_views.sql
```

### Step 8: Deploy

Click **Create Web Service**. Render will automatically deploy.

Access at: https://smartbi-xxxx.onrender.com

## 4. Railway Deployment

### Step 1: Prepare Repository

Same as Render - push to GitHub.

### Step 2: Create Railway Account

1. Sign up at https://railway.app
2. Connect GitHub account

### Step 3: Create New Project

1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Choose your repository

### Step 4: Add PostgreSQL (Optional)

If not using Neon:
1. Click **New** > **Database** > **PostgreSQL**
2. Railway auto-configures `DATABASE_URL`

### Step 5: Configure Environment Variables

```
SMARTBI_SECRET_KEY=your-production-secret-key
SMARTBI_DATABASE_URL=${{Postgres.DATABASE_URL}}  # If using Railway DB
SMARTBI_ADMIN_USERNAME=admin
SMARTBI_ADMIN_PASSWORD=secure-production-password
SMARTBI_UPLOAD_FOLDER=/app/uploads
SMARTBI_CLEANED_FOLDER=/app/cleaned
SMARTBI_PROCESSED_FOLDER=/app/processed
SMARTBI_ORIGINAL_FOLDER=/app/original
SMARTBI_MAX_UPLOAD_BYTES=26214400
```

### Step 6: Add Procfile

Create `Procfile` in root:

```
web: gunicorn -b 0.0.0.0:$PORT run:app
```

### Step 7: Deploy

Railway auto-deploys on push to main branch.

## 5. Docker Deployment

### Step 1: Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p backend/uploads backend/cleaned backend/processed backend/original

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "run.py"]
```

### Step 2: Create docker-compose.yml (Optional)

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SMARTBI_SECRET_KEY=${SMARTBI_SECRET_KEY}
      - SMARTBI_DATABASE_URL=${SMARTBI_DATABASE_URL}
      - SMARTBI_ADMIN_USERNAME=${SMARTBI_ADMIN_USERNAME}
      - SMARTBI_ADMIN_PASSWORD=${SMARTBI_ADMIN_PASSWORD}
    volumes:
      - uploads:/app/backend/uploads
      - cleaned:/app/backend/cleaned
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=smartbi
      - POSTGRES_USER=smartbi
      - POSTGRES_PASSWORD=smartbi123
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/schema.sql:/docker-entrypoint-initdb.d/1-schema.sql
      - ./sql/powerbi_views.sql:/docker-entrypoint-initdb.d/2-views.sql
    ports:
      - "5432:5432"

volumes:
  postgres_data:
  uploads:
  cleaned:
```

### Step 3: Build and Run

```bash
# Using Docker
docker build -t smartbi .
docker run -p 5000:5000 --env-file .env smartbi

# Using Docker Compose
docker-compose up -d
```

### Step 4: Access Application

http://localhost:5000

## 6. Production Considerations

### Security

1. **Change default credentials**
   ```env
   SMARTBI_ADMIN_USERNAME=your-admin-username
   SMARTBI_ADMIN_PASSWORD=strong-random-password
   ```

2. **Use strong secret key**
   ```python
   import secrets
   secrets.token_hex(32)
   ```

3. **Enable HTTPS**
   - Use reverse proxy (nginx, Caddy)
   - Configure SSL certificates
   - Force HTTPS redirects

4. **Database security**
   - Use connection pooling
   - Enable SSL for database connections
   - Restrict database access by IP

### Performance

1. **Use production WSGI server**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

2. **Configure workers**
   ```bash
   # Workers = 2 * CPU cores + 1
   gunicorn -w 5 -b 0.0.0.0:5000 --timeout 120 run:app
   ```

3. **Add caching**
   - Redis for session storage
   - Flask-Caching for query results

4. **Database optimization**
   - Verify indexes from schema.sql
   - Monitor slow queries
   - Use connection pooling

### File Storage

For production with persistent storage:

1. **AWS S3**
   ```python
   import boto3
   # Configure S3 bucket for uploads
   ```

2. **Azure Blob Storage**
   ```python
   from azure.storage.blob import BlobServiceClient
   ```

3. **Google Cloud Storage**
   ```python
   from google.cloud import storage
   ```

### Monitoring

1. **Application logs**
   ```python
   import logging
   logging.basicConfig(filename='app.log', level=logging.INFO)
   ```

2. **Error tracking**
   - Sentry integration
   - Rollbar
   - New Relic

3. **Uptime monitoring**
   - UptimeRobot
   - Pingdom
   - StatusCake

### Backup

1. **Database backups**
   ```bash
   pg_dump -h host -U user -d smartbi > backup.sql
   ```

2. **Automated backups**
   - Neon automatic backups
   - Render/Railway backup features
   - Custom cron jobs

### Scaling

1. **Horizontal scaling**
   - Multiple web instances
   - Load balancer
   - Shared session storage (Redis)

2. **Database scaling**
   - Connection pooling (PgBouncer)
   - Read replicas
   - Query optimization

3. **File storage scaling**
   - CDN for static assets
   - Object storage (S3, Azure, GCS)
   - Separate upload processing workers

## 7. Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql -h host -U user -d smartbi -c "SELECT 1"

# Check environment variables
echo $SMARTBI_DATABASE_URL
```

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Permission Errors

```bash
# Create directories
mkdir -p backend/uploads backend/cleaned backend/processed backend/original
chmod 755 backend/uploads backend/cleaned backend/processed backend/original
```

### File Upload Issues

- Check `SMARTBI_MAX_UPLOAD_BYTES`
- Verify upload folder exists and is writable
- Check disk space

## 8. Health Checks

Test deployment:

```bash
# Health check
curl http://localhost:5000/api/health

# Expected response
{"status": "ok", "service": "SmartBI"}
```

## 9. Rollback

If deployment fails:

1. **Git rollback**
   ```bash
   git revert HEAD
   git push
   ```

2. **Database rollback**
   ```bash
   psql -h host -U user -d smartbi < backup.sql
   ```

3. **Platform rollback**
   - Render: Use "Rollback" button
   - Railway: Redeploy previous version
   - Docker: `docker run` previous image

---

For additional help, refer to:
- [README.md](README.md)
- [SECURITY.md](SECURITY.md)
- Platform documentation (Render, Railway, Docker)
