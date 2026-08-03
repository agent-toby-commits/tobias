FROM python:3.12-slim

WORKDIR /app

COPY apps/tooling/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/tooling ./apps/tooling

EXPOSE 8504

CMD ["streamlit", "run", "apps/tooling/app.py", "--server.address=0.0.0.0", "--server.port=8504", "--server.headless=true", "--server.baseUrlPath=apps/tooling"]
