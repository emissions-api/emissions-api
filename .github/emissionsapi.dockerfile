FROM registry.hub.docker.com/library/centos:8

# Prerequites
RUN dnf install -y epel-release 'dnf-command(config-manager)'
RUN dnf -qy module disable postgresql
RUN dnf -y config-manager --set-enabled powertools
RUN dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm
RUN dnf install -y git gcc make libcurl-devel python38-devel python38 postgresql12-devel openssl-devel

# Create user
RUN useradd --create-home --home-dir /opt/emissions-api --system emissions-api

# Install emissionsapi
WORKDIR /opt/emissions-api/
COPY . emissions-api
RUN python3.8 -m venv venv
RUN PATH=$PATH:/usr/pgsql-12/bin venv/bin/pip install -r emissions-api/requirements.txt
RUN (cd emissions-api && ../venv/bin/python setup.py install)
RUN cp emissions-api/.github/emissionsapi.yml .

# Run
USER emissions-api
CMD ["/opt/emissions-api/venv/bin/gunicorn", "--timeout", "120", "--log-level", "INFO", "--bind", "0.0.0.0:8000", "emissionsapi.web:app"]
