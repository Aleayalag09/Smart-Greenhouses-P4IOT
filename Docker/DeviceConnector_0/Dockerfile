# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /device_connector
WORKDIR /device_connector_0

# Copy the current directory contents into the container at /device_connector
COPY . /device_connector_0

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV NAME World

# Run DeviceConnector.py when the container launches
CMD ["python", "DeviceConnector.py"]