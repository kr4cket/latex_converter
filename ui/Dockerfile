FROM latex_converter_base:v0.0.1
WORKDIR /app
ENV STREAMLIT_SERVER_PORT=8501
CMD ["streamlit", "run", "ui/app.py", "--server.headless", "true"]