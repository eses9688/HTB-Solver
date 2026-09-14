FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends sudo tar coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash svc-report

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY backup.sh /opt/es/maintenance/backup.sh

RUN mkdir -p /var/es/reports /root/backups \
    && chown svc-report:svc-report /var/es/reports \
    && chmod 755 /opt/es/maintenance/backup.sh \
    && chmod 700 /root/backups

RUN printf 'svc-report ALL=(root) NOPASSWD: /opt/es/maintenance/backup.sh\nDefaults:svc-report !requiretty\n' \
      > /etc/sudoers.d/es-backup \
    && chmod 440 /etc/sudoers.d/es-backup

# Stage3 중간 flag - 백엔드 RCE(svc-report) 획득 후에만 읽을 수 있음
RUN echo 'esfg{UjJWMGRHbHVaeUIzWVhKdFpYSXVJRU5vWldOcklIZG9ZWFFnZEdocGN5QnphR1ZzYkNCallXNGdjM1ZrYnk0PQ==}' \
      > /home/svc-report/stage3_note.txt \
    && chown svc-report:svc-report /home/svc-report/stage3_note.txt \
    && chmod 600 /home/svc-report/stage3_note.txt

# Stage4 최종 flag - root만 읽을 수 있음
RUN echo 'esfg{VjJWc2JDQmtiMjVsSVNCRlV5QkVaWFpQY0hNZ1VHeGhkR1p2Y20wZ1RHRmlNeUJqYkdWaGNpND0=}' \
      > /root/flag.txt \
    && chmod 600 /root/flag.txt

EXPOSE 8000
USER svc-report
CMD ["python", "app.py"]
