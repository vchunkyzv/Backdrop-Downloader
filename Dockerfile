# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application files
COPY . .

# Install required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8500 for the web interface
EXPOSE 8500

# Set the command to run the Flask app
CMD ["python", "backdrop_downloader.py"]
