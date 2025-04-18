FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker script
COPY worker.py .

# Command to run the worker
CMD ["python", "worker.py"]