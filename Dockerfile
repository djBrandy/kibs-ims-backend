# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code to /app
COPY . .

# Expose port 5000 (adjust if your app uses a different port)
EXPOSE 5000

# Set an environment variable for production (optional)
ENV FLASK_ENV production

# Start the Flask app using gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]