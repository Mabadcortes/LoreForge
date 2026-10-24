# Use an official, lightweight Python runtime as the parent image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Step 1: Copy only dependency manifests to leverage Docker layer caching
COPY requirements.txt .

# Step 2: Install dependencies without storing pip cache to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Step 3: Copy the rest of the application source code
COPY ./app ./app

# Expose the port that FastAPI runs on
EXPOSE 8000

# Run Uvicorn with hot-reload enabled for active development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]