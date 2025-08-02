# Use Python 3.9 slim as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including OpenSCAD and X11 for headless rendering
RUN apt-get update && apt-get install -y \
    openscad \
    xvfb \
    x11-xserver-utils \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && openscad --version

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with trusted hosts for SSL issues
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output uploads

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DOCKER_CONTAINER=true

# Run the application
CMD ["python", "app.py"]