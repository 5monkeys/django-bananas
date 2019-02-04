ARG PYTHON=3
FROM python:${PYTHON}

# Install system dependencies
ARG DJANGO=">=2.0.9,<2.1"
RUN apt-get update && apt-get install -y \
        gettext && \
    pip install --pre "Django${DJANGO}"

# Install requirements
COPY example/requirements.txt /tmp/
RUN pip install --pre -r /tmp/requirements.txt

# Install bananas source
WORKDIR /usr/src
COPY . django-bananas
RUN pip install -e django-bananas && \
    rm -rf /usr/src/django-bananas/example && \
    mkdir /app

# Install example app
WORKDIR /app
COPY example ./

ENTRYPOINT ["python", "manage.py"]
