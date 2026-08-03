FROM python:3.12-slim

WORKDIR /app

COPY apps/rag/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/rag ./apps/rag

EXPOSE 8501

CMD ["streamlit", "run", "apps/rag/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--server.baseUrlPath=apps/rag"]
