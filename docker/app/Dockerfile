############
### Base ###
############
FROM debian:bookworm AS base
MAINTAINER gm@gm.lv

# Avoid interactive cli blockers
ENV DEBIAN_FRONTEND=noninteractive

# Install OS dependecies
RUN apt-get update -yq \
    && apt-get install -yq --no-install-recommends apt-utils

RUN apt-get install -yq --no-install-recommends \
    apt-transport-https lsb-release ca-certificates gnupg pkg-config \
    less nano curl wget unzip build-essential \
    libmariadb-dev libpq-dev freetds-dev freetds-bin libssl-dev libkrb5-dev \
    libxml2-dev libxslt-dev

# Install python
RUN apt-get -yq --no-install-recommends install \
    python3 python3-pip python3-venv python3-dev

# Create virtualenv
RUN python3 -m venv /srv/venv

# Activate virtual environment
ENV PATH="/srv/venv/bin:$PATH"

# Copy files
RUN mkdir -p /root/meta/data
COPY ./docker/app/scripts /root/meta/scripts

# Clean up caches
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

###################
### Development ###
###################
FROM base AS development

# Args
ARG GIT_NAME
ARG GIT_EMAIL

# Install additional dependecies
RUN apt-get update -yq \
    && apt-get install -yq --no-install-recommends openssh-client tree less git \
        rsync gettext-base

# Setup git
RUN git config --global user.email "$GIT_NAME" \
    && git config --global user.name "$GIT_EMAIL" \
    && git config --global pull.rebase true

# Install python app's dev dependecies
# * For now this is in run script as src is not mounted at build time
# RUN python3 -m pip install -e ./src/database_wrapper/[dev]

# Clean up caches
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Set runtime stuff
WORKDIR /srv/app
CMD ["/root/meta/scripts/run.bash"]


##################
### Deployment ###
##################
FROM base AS deploy

# Copy whole app into container
COPY . /srv/app

# Set runtime stuff
WORKDIR /srv/app
