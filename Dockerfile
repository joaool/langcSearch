FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY langcSearch.py serper_tool.py ./

EXPOSE 8501

CMD streamlit run langcSearch.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
