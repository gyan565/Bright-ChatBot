# Python ka official image use kar rahe hain
FROM python:3.9-slim

# Working directory set karo
WORKDIR /app

# Requirements file copy karo aur install karo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code copy karo
COPY . .

# Bot start karne ka command
CMD ["python", "main.py"]
