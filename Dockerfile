# Use the official Python image as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application files
COPY . /app

# Install required dependencies
RUN pip install flask requests

# Expose port 8500 for the web interface
EXPOSE 8500

# Command to run the application
CMD ["python", "backdrop_downloader.py"]


































