# Quick Setup Script
# Run this to start the vulnerable lab

#!/bin/bash

echo "=== Vulnerable Web Application Setup ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Navigate to the vulnerable-webapp directory
cd "$(dirname "$0")/vulnerable-webapp"

echo "Starting vulnerable web application..."
docker compose up -d

echo ""
echo "=== Services Started ==="
echo ""
echo "Main App:       http://localhost:5000"
echo "WordPress:      http://localhost:8080"
echo "MySQL:          localhost:3306"
echo "FTP:            localhost:21"
echo "SSH:            localhost:2222"
echo ""
echo "=== Default Credentials ==="
echo ""
echo "Flask App:"
echo "  admin / admin"
echo "  user / password"
echo "  test / test123"
echo ""
echo "MySQL:"
echo "  vulnuser / vulnpass"
echo ""
echo "FTP:"
echo "  ftpuser / ftppass123"
echo ""
echo "SSH:"
echo "  sshuser / sshpass123"
echo ""
echo "=== Quick Test Commands ==="
echo ""
echo "Nmap:          nmap -sV localhost"
echo "Nikto:         nikto -h http://localhost:5000"
echo "Gobuster:      gobuster dir -u http://localhost:5000 -w /usr/share/wordlists/dirb/common.txt"
echo "SQLmap:        sqlmap -u \"http://localhost:5000/messages?sender=admin\" --dbs"
echo "Hydra SSH:     hydra -l sshuser -P /usr/share/wordlists/rockyou.txt ssh://localhost:2222"
echo "Hydra FTP:     hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt ftp://localhost"
echo ""
echo "=== To Stop ==="
echo "docker compose down -v"
echo ""
