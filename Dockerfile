# Use the official Python image as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install gcc and other build dependencies
RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]