# SmartBI Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Features

### Authentication
- Session-based authentication
- Admin login required for all operations
- Session timeout after inactivity
- Logout functionality

### Input Validation
- File type validation (.xlsx, .xls only)
- File size limits (25MB default)
- SQL injection prevention with parameterized queries
- XSS protection with input sanitization

### Data Protection
- Environment variable configuration for sensitive data
- Database credentials never exposed in code
- Session data stored securely
- Password hashing recommended for production

### File Security
- Allowed file extensions whitelist
- File content validation
- Temporary file cleanup
- Upload size restrictions

## Security Best Practices

### 1. Change Default Credentials

**CRITICAL**: Change default admin credentials before deployment:

```env
SMARTBI_ADMIN_USERNAME=your-secure-username
SMARTBI_ADMIN_PASSWORD=your-strong-password-here
```

Generate strong passwords:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 2. Use Strong Secret Key

Never use the default secret key in production:

```python
import secrets
print(secrets.token_hex(32))
```

Update `.env`:
```env
SMARTBI_SECRET_KEY=your-generated-secret-key-here
```

### 3. Secure Database Connection

Use SSL for database connections:

```env
SMARTBI_DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

For Neon:
- SSL is enabled by default
- Use connection pooling (PgBouncer)
- Restrict IP access when possible

### 4. Enable HTTPS

Configure HTTPS in production:

**Using nginx:**
```nginx
server {
    listen 443 ssl;
    server_name smartbi.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Using Flask-Talisman:**
```python
from flask_talisman import Talisman
Talisman(app, force_https=True)
```

### 5. Implement Rate Limiting

Add Flask-Limiter to prevent brute force attacks:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@auth_bp.post("/login")
@limiter.limit("5 per minute")
def login():
    # login logic
```

### 6. Add CSRF Protection

Install Flask-WTF for CSRF protection:

```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

### 7. Secure Session Configuration

Update `config.py`:

```python
class Config:
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
```

### 8. Password Hashing

Implement password hashing with bcrypt:

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
hashed = generate_password_hash('admin123')

# Verify password
if check_password_hash(hashed, password):
    # login successful
```

### 9. Input Sanitization

Sanitize all user inputs:

```python
import bleach

def sanitize_input(text):
    return bleach.clean(text, strip=True)
```

### 10. Database Security

- Use parameterized queries (already implemented)
- Limit database user permissions
- Regular security audits
- Monitor for suspicious activity

## Known Security Considerations

### 1. Session Storage

Current implementation uses Flask default sessions (client-side cookies).

**Production recommendation**: Use server-side sessions with Redis:

```python
from flask_session import Session
import redis

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
Session(app)
```

### 2. File Upload Vulnerabilities

Current protections:
- File extension validation
- Size limits
- Content type checking

**Additional recommendations**:
- Virus scanning (ClamAV)
- File content validation
- Separate upload storage
- Content-Disposition headers

### 3. SQL Injection

**Protection**: All queries use parameterized statements via psycopg2.

Example:
```python
cursor.execute("SELECT * FROM uploads WHERE id = %s", (upload_id,))
```

### 4. XSS (Cross-Site Scripting)

**Protection**: 
- Input validation on backend
- Output escaping in frontend
- Content Security Policy headers

Add CSP headers:
```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

### 5. Authentication

Current: Basic session-based authentication

**Enhancement recommendations**:
- Multi-factor authentication (2FA)
- OAuth2/OIDC integration
- JWT tokens for API access
- Password complexity requirements
- Account lockout after failed attempts

## Reporting a Vulnerability

If you discover a security vulnerability, please follow responsible disclosure:

1. **DO NOT** create a public GitHub issue
2. Email security concerns to: security@smartbi.example.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work on a fix.

## Security Checklist for Production

- [ ] Changed default admin credentials
- [ ] Generated strong secret key
- [ ] Enabled HTTPS/SSL
- [ ] Configured secure session cookies
- [ ] Implemented password hashing
- [ ] Added rate limiting
- [ ] Enabled CSRF protection
- [ ] Configured CSP headers
- [ ] Database SSL enabled
- [ ] Restricted database user permissions
- [ ] Implemented logging and monitoring
- [ ] Regular dependency updates
- [ ] Backup strategy in place
- [ ] Security headers configured
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive info
- [ ] File uploads restricted and validated
- [ ] API rate limiting implemented
- [ ] CORS configured properly
- [ ] Regular security audits scheduled

## Security Headers

Implement security headers:

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

## Dependency Security

Regularly check for vulnerabilities:

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade package-name
```

## Logging and Monitoring

Log security events:

```python
import logging

# Log authentication attempts
logger.info(f"Login attempt from {request.remote_addr}")
logger.warning(f"Failed login for {username}")

# Log suspicious activity
logger.error(f"SQL injection attempt detected: {query}")
```

Monitor:
- Failed login attempts
- Unusual upload patterns
- Large file uploads
- Database query patterns
- API usage patterns

## Incident Response Plan

1. **Detection**: Monitor logs and alerts
2. **Analysis**: Investigate the incident
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove the threat
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Document and improve

## Compliance

Ensure compliance with:
- GDPR (if handling EU data)
- CCPA (if handling California data)
- HIPAA (if handling healthcare data)
- PCI DSS (if handling payment data)

## Regular Security Tasks

### Daily
- Monitor application logs
- Check for failed login attempts

### Weekly
- Review access logs
- Check for unusual activity
- Update dependencies

### Monthly
- Security audit
- Review user permissions
- Test backup restoration
- Update security documentation

### Quarterly
- Penetration testing
- Security training for team
- Review and update security policies
- Compliance audit

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

For questions about security, contact: security@smartbi.example.com
