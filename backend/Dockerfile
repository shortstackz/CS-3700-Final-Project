FROM python:3.10-slim
# Use a lightweight Python 3.10 base image
# 'slim' reduces image size while retaining core functionality
WORKDIR /app
# Set the working directory inside the container
# All subsequent commands will run from /app
COPY requirements.txt .
# Install Python dependencies required by the backend
# Uses system-wide installation inside the container
RUN pip install -r requirements.txt

COPY . .
# Declare a mount point for persistent application data
# Used for data that should survive container restarts
VOLUME /app/data
# Expose the Flask application port
# Documents the intended network interface for the container
EXPOSE 5000
# Define the container entrypoint
# Starts the Flask-SocketIO backend application
CMD ["python", "app.py"]
