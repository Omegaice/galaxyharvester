# Install uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy the project into the image
ADD . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

FROM python:3.12-slim-bookworm

# install server and app dependencies
RUN apt update && apt install -y apache2 apache2-utils && apt clean

# enable CGI mods for apache2 server
COPY .docker/apache2.conf /etc/apache2/apache2.conf
RUN a2enmod cgi && a2enmod cgid && service apache2 restart

# set working directory to apache2 default location
WORKDIR /var/www

# Copy the application from the builder
COPY --from=builder --chown=app:app /app /var/www

# Place executables in the environment at the front of the path
ENV PATH="/var/www/.venv/bin:$PATH"

# allow temp folder to be written to (blog, etc.)
RUN mkdir -p /var/www/html/temp && chmod 777 /var/www/html/temp

EXPOSE 80
RUN chmod +x /var/www/.docker/run.sh
RUN ls -lah . && pwd
CMD [ "/var/www/.docker/run.sh" ]
