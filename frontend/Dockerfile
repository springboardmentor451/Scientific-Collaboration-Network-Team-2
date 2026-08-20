FROM python:3.13-slim

WORKDIR /workspace

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=app.py
ENV BACKEND_URL=http://backend:8000/api/v1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
