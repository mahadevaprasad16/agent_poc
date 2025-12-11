# Use the official Python base image
FROM python:3.12-slim

# Set environment variables for Streamlit and the Python application
ENV PYTHONUNBUFFERED 1
ENV STREAMLIT_SERVER_PORT=8080
ENV PORT=8080

# Expose the port the app will run on
EXPOSE 8080

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the Streamlit application
CMD ["streamlit", "run", "agent_poc.py", "--server.port=8080", "--server.address=0.0.0.0"]