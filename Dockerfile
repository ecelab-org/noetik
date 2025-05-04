FROM python:3.11-slim

# Update system packages to fix vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the rest of the application code into the container
COPY . .

# Install the package in editable mode
RUN pip install -e .

# Expose the port for API mode
EXPOSE 8000

# Command to run the main program
CMD ["python", "-m", "noetik.main"]
