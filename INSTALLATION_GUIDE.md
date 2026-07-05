# SmartBI Installation Guide

Step-by-step installation instructions for SmartBI on Windows, Linux, and macOS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Windows Installation](#windows-installation)
3. [Linux Installation](#linux-installation)
4. [macOS Installation](#macos-installation)
5. [Database Setup](#database-setup)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python**: 3.10 or higher
  - Check: `python --version` or `python3 --version`
  - Download: https://www.python.org/downloads/

- **pip**: Python package installer (usually comes with Python)
  - Check: `pip --version` or `pip3 --version`

- **PostgreSQL Client** (for database initialization)
  - Windows: https://www.postgresql.org/download/windows/
  - Linux: `sudo apt install postgresql-client` (Ubuntu/Debian)
  - macOS: `brew install postgresql`

- **Git** (optional, for cloning repository)
  - Check: `git --version`
  - Download: https://git-scm.com/downloads

### Recommended Software

- **Virtual Environment**: venv or virtualenv
- **Code Editor**: VS Code, PyCharm, Sublime Text
- **Database GUI**: pgAdmin, DBeaver, DataGrip
- **API Testing**: Postman, Insomnia, curl

## Windows Installation

### Step 1: Install Python

1. Download Python 3.10+ from https://www.python.org/downloads/
2. Run installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

### Step 2: Get SmartBI Code

**Option A: Clone with Git**
```cmd
git clone https://github.com/yourusername/smartbi.git
cd smartbi
```

**Option B: Download ZIP**
1. Download ZIP from GitHub
2. Extract to desired location
3. Open Command Prompt in that folder

### Step 3: Create Virtual Environment

```cmd
python -m venv venv
```

### Step 4: Activate Virtual Environment

```cmd
venv\Scripts\activate
```

You should see `(venv)` in your prompt.

### Step 5: Install Dependencies

```cmd
pip install -r requirements.txt
```

If you encounter errors:
```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Create Required Directories

```cmd
mkdir backend\uploads
mkdir backend\cleaned
mkdir backend\processed
mkdir backend\original
```

### Step 7: Configure Environment

```cmd
copy .env.example .env
notepad .env
```

Edit the values (see [Configuration](#configuration) section).

### Step 8: Setup Database

See [Database Setup](#database-setup) section.

### Step 9: Run Application

```cmd
python run.py
```

Access at: http://localhost:5000

## Linux Installation

### Step 1: Install Python

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
```

Verify:
```bash
python3 --version
pip3 --version
```

### Step 2: Install PostgreSQL Client

**Ubuntu/Debian:**
```bash
sudo apt install postgresql-client
```

**Fedora/RHEL:**
```bash
sudo dnf install postgresql
```

**Arch Linux:**
```bash
sudo pacman -S postgresql-libs
```

### Step 3: Get SmartBI Code

```bash
git clone https://github.com/yourusername/smartbi.git
cd smartbi
```

Or download and extract ZIP.

### Step 4: Create Virtual Environment

```bash
python3 -m venv venv
```

### Step 5: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Create Required Directories

```bash
mkdir -p backend/uploads backend/cleaned backend/processed backend/original
```

### Step 8: Configure Environment

```bash
cp .env.example .env
nano .env  # or vim .env or gedit .env
```

Edit the values (see [Configuration](#configuration) section).

### Step 9: Setup Database

See [Database Setup](#database-setup) section.

### Step 10: Run Application

```bash
python run.py
```

Access at: http://localhost:5000

## macOS Installation

### Step 1: Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Python

```bash
brew install python@3.11
```

Verify:
```bash
python3 --version
pip3 --version
```

### Step 3: Install PostgreSQL Client

```bash
brew install postgresql
```

### Step 4: Get SmartBI Code

```bash
git clone https://github.com/yourusername/smartbi.git
cd smartbi
```

### Step 5: Create Virtual Environment

```bash
python3 -m venv venv
```

### Step 6: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 7: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 8: Create Required Directories

```bash
mkdir -p backend/uploads backend/cleaned backend/processed backend/original
```

### Step 9: Configure Environment

```bash
cp .env.example .env
nano .env
```

Edit the values (see [Configuration](#configuration) section).

### Step 10: Setup Database

See [Database Setup](#database-setup) section.

### Step 11: Run Application

```bash
python run.py
```

Access at: http://localhost:5000

## Database Setup

### Option 1: Neon Serverless PostgreSQL (Recommended)

1. **Create Account**
   - Visit https://neon.tech
   - Sign up for free account

2. **Create Project**
   - Click "New Project"
   - Choose a name: "SmartBI"
   - Select region closest to you
   - Click "Create"

3. **Get Connection String**
   - Copy the connection string
   - Format: `postgresql://user:password@host/database?sslmode=require`

4. **Initialize Schema**
   ```bash
   # Using psql (Windows)
   psql "postgresql://user:pass@host/smartbi?sslmode=require" -f sql/schema.sql
   psql "postgresql://user:pass@host/smartbi?sslmode=require" -f sql/powerbi_views.sql
   
   # Using psql (Linux/Mac)
   psql 'postgresql://user:pass@host/smartbi?sslmode=require' -f sql/schema.sql
   psql 'postgresql://user:pass@host/smartbi?sslmode=require' -f sql/powerbi_views.sql
   ```

5. **Update .env**
   ```env
   SMARTBI_DATABASE_URL=postgresql://user:pass@host/smartbi?sslmode=require
   ```

### Option 2: Local PostgreSQL

1. **Install PostgreSQL**
   - Windows: https://www.postgresql.org/download/windows/
   - Linux: `sudo apt install postgresql postgresql-contrib`
   - macOS: `brew install postgresql`

2. **Start PostgreSQL Service**
   ```bash
   # Windows (as Administrator)
   net start postgresql-x64-15
   
   # Linux
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   
   # macOS
   brew services start postgresql
   ```

3. **Create Database**
   ```bash
   # Linux/macOS
   sudo -u postgres createdb smartbi
   sudo -u postgres createuser smartbi_user
   sudo -u postgres psql
   
   # In psql:
   ALTER USER smartbi_user WITH PASSWORD 'smartbi123';
   GRANT ALL PRIVILEGES ON DATABASE smartbi TO smartbi_user;
   \q
   ```

   ```cmd
   # Windows
   psql -U postgres
   CREATE DATABASE smartbi;
   CREATE USER smartbi_user WITH PASSWORD 'smartbi123';
   GRANT ALL PRIVILEGES ON DATABASE smartbi TO smartbi_user;
   \q
   ```

4. **Initialize Schema**
   ```bash
   psql -U smartbi_user -d smartbi -f sql/schema.sql
   psql -U smartbi_user -d smartbi -f sql/powerbi_views.sql
   ```

5. **Update .env**
   ```env
   SMARTBI_DATABASE_URL=postgresql://smartbi_user:smartbi123@localhost:5432/smartbi
   ```

### Option 3: Using Database GUI

1. Open pgAdmin, DBeaver, or DataGrip
2. Create new connection to your PostgreSQL server
3. Create database named "smartbi"
4. Open SQL editor
5. Execute `sql/schema.sql`
6. Execute `sql/powerbi_views.sql`
7. Update `.env` with connection string

## Configuration

Edit `.env` file with your settings:

```env
# Required: Generate a strong secret key
SMARTBI_SECRET_KEY=your-secret-key-change-this-in-production

# Required: Database connection string
SMARTBI_DATABASE_URL=postgresql://user:password@host:port/smartbi

# Required: Admin credentials (CHANGE THESE!)
SMARTBI_ADMIN_USERNAME=admin
SMARTBI_ADMIN_PASSWORD=change-this-secure-password

# Optional: File storage paths (relative or absolute)
SMARTBI_UPLOAD_FOLDER=backend/uploads
SMARTBI_CLEANED_FOLDER=backend/cleaned
SMARTBI_PROCESSED_FOLDER=backend/processed
SMARTBI_ORIGINAL_FOLDER=backend/original

# Optional: Max upload size in bytes (default: 25MB)
SMARTBI_MAX_UPLOAD_BYTES=26214400
```

### Generate Secret Key

**Python:**
```python
import secrets
print(secrets.token_hex(32))
```

**Online:** Use https://randomkeygen.com/

### Security Recommendations

- ✅ Change default admin password
- ✅ Use strong secret key (64+ characters)
- ✅ Use environment-specific .env files
- ✅ Never commit .env to version control
- ✅ Use HTTPS in production
- ✅ Enable database SSL

## Running the Application

### Development Mode

**Windows:**
```cmd
venv\Scripts\activate
python run.py
```

**Linux/macOS:**
```bash
source venv/bin/activate
python run.py
```

Access at: http://localhost:5000

Default credentials:
- Username: admin
- Password: admin123 (change in .env)

### Production Mode

Use a production WSGI server:

**Install gunicorn:**
```bash
pip install gunicorn
```

**Run with gunicorn:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

For more deployment options, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Verification

### 1. Check Application Status

Visit: http://localhost:5000

You should see the SmartBI landing page.

### 2. Test API Health

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{"status": "ok", "service": "SmartBI"}
```

### 3. Test Login

1. Open http://localhost:5000
2. Enter admin credentials
3. Click "Sign In"
4. Should see "Authenticated" message

### 4. Test Upload

1. Navigate to Upload page
2. Select a sample Excel file from `sample_data/generated/`
3. Click Upload
4. Should see processing status

### 5. Test Dashboard

1. Navigate to Dashboard page
2. Should see KPIs and charts
3. Try filtering data

### 6. Test Database Connection

```bash
# Using psql
psql "$SMARTBI_DATABASE_URL" -c "SELECT COUNT(*) FROM smartbi_uploads;"

# Expected: Number of uploads (0 if fresh install)
```

### 7. Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

Expected: All tests pass

## Troubleshooting

### Issue: Python not found

**Windows:**
```cmd
# Add Python to PATH manually
setx PATH "%PATH%;C:\Python311;C:\Python311\Scripts"
```

**Linux/macOS:**
```bash
# Use python3 explicitly
alias python=python3
alias pip=pip3
```

### Issue: pip install fails

**Solution 1: Upgrade pip**
```bash
python -m pip install --upgrade pip
```

**Solution 2: Install with --user**
```bash
pip install --user -r requirements.txt
```

**Solution 3: Install individually**
```bash
pip install flask pandas openpyxl psycopg2-binary reportlab pytest python-dotenv
```

### Issue: psycopg2 installation fails

**Windows:**
```cmd
pip install psycopg2-binary
```

**Linux:**
```bash
# Install PostgreSQL development files
sudo apt install libpq-dev python3-dev
pip install psycopg2-binary
```

### Issue: Permission denied on directories

**Windows:**
```cmd
icacls backend /grant Users:F /t
```

**Linux/macOS:**
```bash
chmod 755 backend/uploads backend/cleaned backend/processed backend/original
```

### Issue: Port 5000 already in use

**Find process using port:**

**Windows:**
```cmd
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Linux/macOS:**
```bash
lsof -i :5000
kill -9 <PID>
```

**Or change port in run.py:**
```python
if __name__ == "__main__":
    app.run(debug=True, port=5001)
```

### Issue: Database connection fails

**Check connection string format:**
```
postgresql://username:password@hostname:port/database
```

**Test connection:**
```bash
psql "your-connection-string-here" -c "SELECT 1;"
```

**Common issues:**
- Wrong credentials
- Database doesn't exist
- PostgreSQL service not running
- Firewall blocking connection
- SSL required but not specified

### Issue: Import errors

**Ensure virtual environment is activated:**
```bash
# You should see (venv) in your prompt
# If not, activate it again

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

**Reinstall dependencies:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: No module named 'app'

**Check you're in the correct directory:**
```bash
# Should be in SmartBI root directory
ls  # Should show run.py, backend/, frontend/, etc.
```

**Or adjust Python path in run.py** (already done in the project).

### Issue: Database tables don't exist

**Run schema scripts:**
```bash
psql "$SMARTBI_DATABASE_URL" -f sql/schema.sql
psql "$SMARTBI_DATABASE_URL" -f sql/powerbi_views.sql
```

### Issue: Uploads fail

**Check directories exist:**
```bash
ls -la backend/
# Should show: uploads/, cleaned/, processed/, original/
```

**Create if missing:**
```bash
mkdir -p backend/uploads backend/cleaned backend/processed backend/original
```

**Check permissions:**
```bash
# Linux/macOS
chmod 755 backend/uploads backend/cleaned backend/processed backend/original

# Windows
# Should work by default
```

## Next Steps

After successful installation:

1. **Change default credentials** in `.env`
2. **Generate sample data**: Run `python sample_data/generate_sample_excels.py`
3. **Upload test files** from `sample_data/generated/`
4. **Explore the dashboard** and analytics features
5. **Review documentation**:
   - [README.md](README.md)
   - [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
   - [USER_MANUAL.md](USER_MANUAL.md)
6. **Setup Power BI**: Follow [powerbi/POWER_BI_GUIDE.md](powerbi/POWER_BI_GUIDE.md)
7. **Run tests**: `pytest backend/tests/`
8. **Plan deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## Getting Help

- **Documentation**: Check docs in `documentation/` folder
- **Issues**: Open issue on GitHub
- **Security**: Email security@smartbi.example.com
- **Community**: Join discussions on GitHub

## Uninstallation

### Remove Application

```bash
# Deactivate virtual environment
deactivate

# Remove project directory
rm -rf smartbi/  # Linux/macOS
rmdir /s smartbi\  # Windows
```

### Remove Database

**Neon:** Delete project in Neon dashboard

**Local PostgreSQL:**
```bash
psql -U postgres
DROP DATABASE smartbi;
DROP USER smartbi_user;
\q
```

---

Successfully installed? Proceed to [README.md](README.md) for usage instructions!
