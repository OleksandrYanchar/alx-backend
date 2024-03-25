FROM python:3.10

# Create a group and user
RUN groupadd -r celerygroup && useradd -r -g celerygroup celeryuser

COPY static/media/avatars/no_avatar.jpg /static/media/avatars/no_avatar.jpg
WORKDIR /app

RUN apt update && apt -qy upgrade

# Copy the entire requirements directory
COPY requirements /app/requirements
# Install dependencies from dev.txt
RUN pip install -r requirements/dev.txt

# Copy the rest of your application
COPY . /app/

# Change ownership of the /app directory
RUN chown -R celeryuser:celerygroup /app

# Use the non-root user to run your application
USER celeryuser

# Set PYTHONPATH to ensure Python imports work correctly
ENV PYTHONPATH /app/app

WORKDIR /app/
