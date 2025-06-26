FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV STREAMLIT_SERVER_PORT=8501
CMD ["streamlit", "run", "ui/app.py", "--server.headless", "true"]