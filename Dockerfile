# Use an official Python runtime as a parent image
FROM python:3.11-alpine

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt requirements.txt

# Install git, then dependencies, then remove git
RUN apk add --no-cache git \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip \
    && apk del git

# Copy the current directory contents into the container at /app
COPY . .

EXPOSE 80

# Run main.py when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]