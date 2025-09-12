FROM python:3.11-slim

# 1) App deps
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY monitor.py .

# 2) Install supercronic (single static binary)
# Latest releases available at https://github.com/aptible/supercronic/releases
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.34/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=e8631edc1775000d119b70fd40339a7238eece14 \
    SUPERCRONIC=supercronic-linux-amd64

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

# 3) Crontab with env expansion (no 'root' column)
# You can keep the schedule configurable via CRON_SCHEDULE
ENV PY_BIN=/usr/local/bin/python
ENV CRON_SCHEDULE="*/1 * * * *"

# Build the crontab at runtime so $CRON_SCHEDULE expands before supercronic parses it
CMD /bin/bash -lc '\
  printf "%s\n" \
    "SHELL=/bin/bash" \
    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    "$CRON_SCHEDULE $PY_BIN -u /app/monitor.py" \
    "$CRON_SCHEDULE echo \"[tick] \$(date -Iseconds)\" " \
    > /etc/supercronic.crontab && \
  exec /usr/local/bin/supercronic -json /etc/supercronic.crontab'
