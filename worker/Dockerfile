FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker scripts
COPY . .

# Create directory for GPX files
RUN mkdir -p gpx

# Command to run the worker
CMD ["python", "worker.py"]