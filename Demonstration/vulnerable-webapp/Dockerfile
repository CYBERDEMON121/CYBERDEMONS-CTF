FROM python:3.9-slim

RUN apt-get update && apt-get install -y smbclient curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt smbprotocol

# Copy application
COPY . .

# Create uploads directory
RUN mkdir -p uploads pages

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
