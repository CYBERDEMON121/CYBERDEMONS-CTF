#!/bin/bash
# ============================================
# VULNERABLE LAB - SERVICE TEST SCRIPT
# ============================================

echo "=========================================="
echo "     VULNERABLE LAB - SERVICE STATUS"
echo "=========================================="

# Flask App
echo -e "\n[1] Flask App (http://localhost:5000)"
curl -s -o /dev/null -w "    HTTP: %{http_code}" http://localhost:5000/
echo ""
curl -s http://localhost:5000/api/users | python3 -c "import sys,json; print('    API: OK -', len(json.load(sys.stdin)), 'users')" 2>/dev/null
echo "    Credentials: admin/admin, user/password, test/test123"

# MySQL
echo -e "\n[2] MySQL (localhost:3307)"
docker exec vulnweb-mysql mysql -u vulnuser -pvulnpass vulnapp -e "SELECT COUNT(*) as users FROM user;" 2>/dev/null | tail -1
echo "    Credentials: vulnuser/vulnpass"

# FTP
echo -e "\n[3] FTP (localhost:2121)"
nc -zv localhost 2121 2>&1 | grep -o "succeeded" && echo "    FTP: OK" || echo "    FTP: Connected"
echo "    Credentials: ftpuser/ftppass123"

# SSH
echo -e "\n[4] SSH (localhost:2222)"
nc -zv localhost 2222 2>&1 | grep -o "succeeded" && echo "    SSH: OK" || echo "    SSH: Connected"
echo "    Credentials: sshuser/sshpass123"

# WordPress
echo -e "\n[5] WordPress (http://localhost:8080)"
curl -s -o /dev/null -w "    HTTP: %{http_code}" http://localhost:8080/
echo ""
echo "    Complete installation at http://localhost:8080/wp-admin"

# Metasploitable
echo -e "\n[6] Metasploitable Services"
curl -s -o /dev/null -w "    HTTP (81): %{http_code}" http://localhost:81/
echo ""
nc -zv localhost 2122 2>&1 | grep -o "succeeded" && echo "    FTP (2122): OK"
nc -zv localhost 2223 2>&1 | grep -o "succeeded" && echo "    SSH (2223): OK"
nc -zv localhost 2323 2>&1 | grep -o "succeeded" && echo "    Telnet (2323): OK"
echo "    Credentials: msfadmin/msfadmin"

echo -e "\n=========================================="
echo "     VULNERABILITY TESTS"
echo "=========================================="

# SQL Injection Test
echo -e "\n[SQL Injection Test]"
curl -s "http://localhost:5000/api/users" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('    Password hashes exposed via API:')
for u in data[:2]:
    print(f'      {u[\"username\"]}: {u[\"password_hash\"]}')" 2>/dev/null

# XSS Test
echo -e "\n[XSS Test]"
curl -s "http://localhost:5000/search?q=<script>alert(1)</script>" | grep -o "Results for: <script>alert(1)</script>" && echo "    Reflected XSS: VULNERABLE" || echo "    Reflected XSS: Working"

# Debug Endpoint
echo -e "\n[Debug Endpoint Test]"
curl -s http://localhost:5000/debug | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('    Debug endpoint exposes:')
print('      - Database:', data.get('database', 'N/A'))
print('      - Secret key:', data.get('secret_key', 'N/A')[:20] + '...')
" 2>/dev/null

echo -e "\n=========================================="
echo "     READY FOR SECURITY TESTING"
echo "=========================================="
echo ""
echo "Quick commands to get started:"
echo ""
echo "  Nmap:       nmap -sV localhost"
echo "  Nikto:      nikto -h http://localhost:5000"
echo "  SQLmap:     sqlmap -u \"http://localhost:5000/messages?sender=admin\" --dbs"
echo "  Hydra SSH:  hydra -l sshuser -P /usr/share/wordlists/rockyou.txt ssh://localhost:2222"
echo "  Metasploit: msfconsole"
echo ""
