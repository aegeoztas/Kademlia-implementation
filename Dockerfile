# Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /DHT5

# Copy the DHT5 directory content inside the container
COPY . /DHT5

# Ensure the required Python packages are installed (if any)
# You can add a requirements.txt file in your project and uncomment the following lines
# COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make the Python files executable
#RUN chmod +x script1.py script2.py

# Use a script to run both Python files in parallel
#CMD ["sh", "-c", "python3 script1.py & python3 script2.py"]
CMD ["sh", "-c", "python3 kademlia_server.py "]
