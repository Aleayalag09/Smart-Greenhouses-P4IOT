# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /environment_manager
WORKDIR /environment_manager

# Copy the current directory contents into the container at /environment_manager
COPY . /environment_manager

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV NAME World

# Run EnvironmentManager.py when the container launches
CMD ["python", "EnvironmentManager.py"]