# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first for better caching
COPY app/requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the setup.py and promptpilot package to install the package
COPY setup.py /setup.py
COPY promptpilot/ /promptpilot/

# Install the promptpilot package
# Navigate to the root directory if necessary
WORKDIR /

# Install promptpilot
RUN pip install --no-cache-dir .

# Copy the rest of the application code
COPY app/ /app/

# Expose the port the app runs on
EXPOSE 5001

# Define the default command to run the application
CMD ["python", "app/app.py"]