# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /resource_catalog
WORKDIR /resource_catalog

# Copy the current directory contents into the container at /resource_catalog
COPY . /resource_catalog

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
# EXPOSE 8080

# Define environment variable
# ENV NAME World

# Run ResourceCatalog.py when the container launches
CMD ["python", "ResourceCatalog.py"]