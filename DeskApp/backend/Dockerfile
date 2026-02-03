# ---- Base image ----
FROM python:3.11-slim

# ---- Set working dir ----
WORKDIR /app

# ---- Install system deps (if needed) ----
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# ---- Copy & install python deps ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy app code ----
COPY . .

# ---- Expose port ----
EXPOSE 3001

# ---- Start server ----
CMD ["python", "main.py"]
