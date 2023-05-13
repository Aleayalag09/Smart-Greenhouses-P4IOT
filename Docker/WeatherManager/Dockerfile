# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /weather_manager
WORKDIR /weather_manager

# Copy the current directory contents into the container at /weather_manager
COPY . /weather_manager

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV NAME World

# Run WeatherManager.py when the container launches
CMD ["python", "WeatherManager.py"]