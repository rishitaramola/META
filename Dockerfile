FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

ENV API_BASE_URL=""
ENV MODEL_NAME=""
ENV GROQ_API_KEY=""
ENV HF_TOKEN=""

CMD ["python", "inference.py"]