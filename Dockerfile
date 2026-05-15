FROM python:3.12-slim-bullseye
ENV CONFIGURATION_FILE_PATH="/etc/config.json"
ENV OUTPUT_DIRECTORY="/etc/config.json"
# Install git
RUN apt update && apt install git -y
# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the application into the container.
COPY garage_bootstrap /garage_bootstrap

# Install the application dependencies.
WORKDIR /garage_bootstrap
RUN uv sync --locked --no-cache

# Run the application.
CMD ["sh", "-c", "uv run garage_bootstrap ${CONFIGURATION_FILE_PATH} ${OUTPUT_DIRECTORY}"]