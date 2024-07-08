FROM python:3.12-slim AS builder
RUN pip install --upgrade pip 
RUN pip install pipx 
ENV PATH="/root/.local/bin:${PATH}"
RUN pipx install poetry
RUN pipx inject poetry poetry-plugin-bundle
WORKDIR /src
COPY . .
RUN poetry bundle venv --only=main /venv

FROM python:3.12-slim AS runtime
COPY --from=builder /venv /venv
RUN chmod +x /venv/bin/thermostatter-api
EXPOSE 8080
ENTRYPOINT ["/venv/bin/thermostatter-api"]