FROM python:3.12-slim

WORKDIR /app

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/api ./apps/api

EXPOSE 8505

CMD ["streamlit", "run", "apps/api/app.py", "--server.address=0.0.0.0", "--server.port=8505", "--server.headless=true", "--server.baseUrlPath=apps/api"]
