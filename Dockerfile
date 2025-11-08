# -----------------------------
# Dockerfile for Employee Attendance Hashing System Backend
# -----------------------------
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy backend files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 7077

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=7077

# Run the application
CMD ["flask", "run"]
