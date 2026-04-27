FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
EXPOSE 5000
RUN mkdir -p /data
ENV DB_PATH=/data/tasks.db
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]