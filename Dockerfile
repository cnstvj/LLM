# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables (override in Defang dashboard for secrets)
ENV FLASK_ENV=production

# Start the server
CMD ["python", "server.py"]
CMD ["python", "gui_modern.py"]
