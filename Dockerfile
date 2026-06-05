# Python ka official image
FROM python:3.9-slim

# Working directory
WORKDIR /app

# Requirements install karo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code copy karo
COPY . .

# 💡 Yeh line zaroori hai (Back4App ko khush karne ke liye)
EXPOSE 8080

# Bot start karo
CMD ["python", "main.py"]
