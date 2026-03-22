# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy cijeli servis
COPY . .

# Expose port 8080
EXPOSE 8080

# Start app
CMD ["python", "app.py"]
