# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

# Start the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]