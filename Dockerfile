FROM python:3.13-slim

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY generated ./generated
COPY server.py auth.py ./
COPY protos ./protos

EXPOSE 50051
CMD ["uv", "run", "--no-sync", "python", "server.py"]