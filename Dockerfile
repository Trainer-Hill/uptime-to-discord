# Use a lightweight base image with Python
FROM python:3.11-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script(s) and .env file
COPY monitor.py .
COPY .env .

# ENV vars (defaults; can be overridden at runtime)
ENV RUN_MODE="cron" \
    CRON_SCHEDULE="5 * * * *"   # default: every 5 minutes

# Entry point
CMD if [ "$RUN_MODE" = "cron" ]; then \
      echo "$CRON_SCHEDULE bash -c 'set -a && . /app/.env && python /app/monitor.py' >> /var/log/cron.log 2>&1" \
        > /etc/cron.d/my-cron && \
      chmod 0644 /etc/cron.d/my-cron && \
      crontab /etc/cron.d/my-cron && \
      touch /var/log/cron.log && \
      cron && tail -f /var/log/cron.log; \
    else \
      set -a && . /app/.env && python /app/monitor.py; \
    fi
