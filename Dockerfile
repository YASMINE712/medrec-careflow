FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py run.py config.py ./
COPY models models
COPY routes routes
COPY utils utils
COPY ml ml
COPY scripts scripts
COPY templates templates
COPY static static
RUN python scripts/create_fixture.py && python -m ml.train && useradd --create-home appuser && mkdir -p instance && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')"
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--call", "app:create_app"]
