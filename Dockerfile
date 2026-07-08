# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    PYTHONUSERBASE="/home/appuser/.local"

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /home/appuser appuser

FROM base AS dependencies

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --user --requirement requirements.txt

FROM base AS runtime

COPY --from=dependencies --chown=appuser:appgroup /home/appuser/.local /home/appuser/.local
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
