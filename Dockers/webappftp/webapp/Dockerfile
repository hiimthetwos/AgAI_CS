# Use the official Python image as the base image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the app's source code into the container
COPY . .

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV FLASK_APP=app.py

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]

