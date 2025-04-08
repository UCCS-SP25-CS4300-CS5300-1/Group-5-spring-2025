# Use an official Python runtime as a parent image
FROM python:3.12

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# # Create a new user with no login shell
# RUN useradd --no-create-home --shell /usr/sbin/nologin appuser

# # Switch to the new user
# USER appuser

# Prevent Python from writing pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

## Dynamically generate some given "SECRET_KEY" var for prod
RUN export SECRET_DJ=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# Copy and install dependencies first for better layer caching
COPY requirements.txt /app/
RUN pip install --upgrade pip

RUN pip install uv && \
    python -m uv pip install -r requirements.txt && \
    python -m uv pip install gunicorn psycopg

# RUN pip install --upgrade pip && pip install -r requirements.txt && \
    # pip install uv gunicorn psycopg

# Copy the rest of the application code
COPY . /app/

# Collect static files for production
RUN python manage.py collectstatic --noinput

# Expose the port your app runs on (adjust as needed)
EXPOSE 8080

# Start the application using gunicorn (update project name and options as needed)
CMD ["gunicorn", "camp_mate.wsgi:application", "--bind", "0.0.0.0:8080"]
