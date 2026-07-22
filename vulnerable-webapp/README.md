# CYBERDEMON CTF - Vulnerable Web Application

Flask-based vulnerable web application with 15 security tool challenges.

## Warning

INTENTIONAL security vulnerabilities. Never deploy on production.

## Quick Start

```bash
cd /home/demonwarrior/Demonstration
docker compose up -d
```

Access at: `http://localhost:5000`

## Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin | admin |
| user | password | user |
| test | test123 | user |
| sqltest | sql123 | user |

## CTF System

- Each tool has a unique flag hidden in a location requiring that tool
- Completed missions disappear from the main list
- Flag submission shows points and redirects to index
- Admin user `DEMON` can reset CTF (exports to JSON first)

## Vulnerability Map

### SQL Injection (SQLmap)
- **Login form**: `/ctf/tool/sqlmap/login` - Authentication bypass
- **API**: `/ctf/tool/sqlmap/api?username=admin' OR '1'='1`
- **Search**: `/ctf/tool/sqlmap/search?username=admin' OR '1'='1`

### Cross-Site Scripting (XSS)
- **Reflected XSS**: `/search?q=<script>alert('XSS')</script>`
- **Stored XSS**: Post content on `/posts`

### Command Injection
- **Ping**: `/ping?host=127.0.0.1; cat /etc/passwd`

### Broken Authentication
- **Weak passwords**: admin/admin, user/password
- **MD5 hashing**: Password hashes easily crackable

### IDOR
- **User profiles**: `/profile?id=1`, `/profile?id=2`

### SSRF
- **URL fetch**: `/fetch?url=http://169.254.169.254/latest/meta-data/`

### Open Redirect
- `/redirect?url=https://evil.com`

## Challenge Endpoints

| Tool | Main Page | Target/Download | Flag |
|------|-----------|-----------------|------|
| Nmap | `/` | HTTP headers | `X-CTF-Flag` header |
| Metasploit | `/ctf/tool/metasploit` | vsftpd on metasploitable | `/ctf/tool/metasploit/flag.txt` |
| Burp Suite | `/ctf/tool/burpsuite` | `/ctf/tool/burpsuite/login` | `X-CTF-Flag` header |
| Wireshark | `/ctf/tool/wireshark` | Send packet button | `X-Secret-Token` header |
| Nikto | `/ctf/tool/nikto` | `/ctf/tool/nikto/login` | `/ctf/tool/nikto/backup.sql` |
| Gobuster | `/ctf/tool/gobuster` | Directory brute-force | `/ctf/tool/gobuster/secret/flag.txt` |
| SQLmap | `/ctf/tool/sqlmap` | `/ctf/tool/sqlmap/api` | Database `flag` table |
| John | `/ctf/tool/john` | `/ctf/tool/john/hash.txt` | `/ctf/tool/john/flag.txt` |
| Hashcat | `/ctf/tool/hashcat` | `/ctf/tool/hashcat/hashes.txt` | `/ctf/tool/hashcat/flag.txt` |
| Hydra | `/ctf/tool/hydra` | SSH on metasploitable | `/ctf/tool/hydra/flag.txt` |
| Responder | `/ctf/tool/responder` | NTLM/SMB buttons | Base64 in hash |
| Netcat | `/ctf/tool/netcat` | FTP banner | `/ftp-banner` |

## File Structure

```
vulnerable-webapp/
├── app.py              # Main Flask application
├── Dockerfile          # Python 3.9 + smbclient + curl
├── docker-compose.yml  # Service definitions
├── requirements.txt    # Flask, SQLAlchemy, etc.
├── passwords.txt       # Hydra wordlist (30 passwords)
├── users.txt           # Hydra user list (11 users)
├── uploads/            # File upload directory
└── instance/           # SQLite database
    └── vulnerable.db
```

## Key Features

- SQLAlchemy ORM with SQLite
- Session-based authentication
- MD5 password hashing (intentionally weak)
- Admin reset with JSON export
- Real SMB/NTLM traffic generation for Responder
- Metasploitable2 with vsftpd 2.3.4 backdoor

## Cleanup

```bash
docker compose down -v
```

## Disclaimer

FOR EDUCATIONAL PURPOSES ONLY. Never test against systems you don't own.
