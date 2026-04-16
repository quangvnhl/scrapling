FROM python:3.11-slim

# Cài đặt các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip show scrapling || true

# Copy code vào
COPY . .

# Chạy trên cổng 7860 (Hugging Face yêu cầu)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]