# Docker Containerization and Deployment

Containerization is the practice of packaging an application and all its dependencies together in a standardized unit called a container. This guarantees the application runs consistently across different computing environments.

## Dockerfile Design
A Dockerfile contains instructions to build a container image. Here is a typical production-grade multi-stage build:
```dockerfile
FROM python:3.11-slim as builder
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose
Compose is a tool for defining and running multi-container Docker applications. With Compose, you use a YAML file to configure your application’s services.

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=google
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./chroma_db:/app/chroma_db
```

## Production Scaling Best Practices
- **Use lightweight base images**: Prefer `slim` or `alpine` variants to reduce security attack surface and build size.
- **Volume persistence**: Ensure databases (SQLite, ChromaDB) are stored on host volumes so data survives container restarts.
- **Port mapping**: Expose only the required ports to the host interface.
