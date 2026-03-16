############
### Base ###
############

FROM debian:trixie-slim AS base

LABEL maintainer="Gints Murans gm@gm.lv"
LABEL description="Docker image for py_db_wrapper library"
LABEL version="0.1"

# Avoid interactive cli blockers
ENV DEBIAN_FRONTEND=noninteractive
ENV MAKEFLAGS=-j6

# Set timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Riga /etc/localtime

# Install OS dependecies and base tools
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends apt-utils

# Install runtime libs and base tools
RUN apt-get install -y --no-install-recommends \
    ca-certificates less nano curl wget unzip tree \
    python3 python3-pip python3-venv locales \
    libmariadb3 libpq5 libsybdb5 libssl3 libkrb5-3 libxml2 libxslt1.1 \
    # * Clean up caches
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Locale
RUN printf "en_US.UTF-8 UTF-8\n" > /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8

# Create virtualenv and upgrade pip
RUN python3 -m venv /srv/venv
ENV PATH="/srv/venv/bin:$PATH"
RUN python3 -m pip install --no-cache-dir --upgrade pip

# Non-root user + chown everything
ARG LOCAL_USER_ID=1000
ARG LOCAL_GROUP_ID=1000
RUN groupadd -g $LOCAL_GROUP_ID appuser \
    && useradd -m -u $LOCAL_USER_ID -g appuser -s /bin/bash appuser \
    && chown -R appuser:appuser /srv/venv

# Meta (root-owned, read-only)
RUN mkdir -p /srv/meta/{data,conf,scripts}
COPY ./docker/app/scripts /srv/meta/scripts

# Clean up caches
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*


###############
### Builder ###
###############

FROM base AS builder

# Install build dependecies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
    build-essential pkg-config python3-dev \
    libmariadb-dev libpq-dev freetds-dev libssl-dev libkrb5-dev \
    libxml2-dev libxslt-dev \
    # * Clean up caches
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*


###################
### Development ###
###################

FROM builder AS development

# Install additional dependecies (still as root for apt)
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
    git openssh-client rsync gettext-base procps \
    # * Clean up caches
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Fix ownership of app dir
RUN mkdir -p /srv/app && chown -R appuser:appuser /srv/app

# Switch to non-root user
USER appuser

# Setup git
ARG GIT_NAME
ARG GIT_EMAIL
RUN git config --global user.email "$GIT_EMAIL" \
    && git config --global user.name "$GIT_NAME" \
    && git config --global pull.rebase true \
    && git config --global safe.directory /srv/app

# Setup bashrc
RUN cat /srv/meta/scripts/bashrc.bash >> ~/.bashrc

# Set runtime stuff
WORKDIR /srv/app
CMD ["/srv/meta/scripts/run.bash"]


##################
### Production ###
##################

FROM base AS production

# Copy python packages from builder
COPY --from=builder --chown=appuser:appuser /srv/venv /srv/venv

# Copy whole app into container
COPY --chown=appuser:appuser . /srv/app

# Switch to non-root user
USER appuser

# Set runtime stuff
WORKDIR /srv/app
