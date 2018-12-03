ARG PYTHON=3
FROM python:${PYTHON}

# Install system dependencies
ARG DJANGO=2.0.3
RUN apt-get update && apt-get install -y \
        gettext && \
    pip install --pre \
        "Django${DJANGO}" \
        "djangorestframework>=3.9.0,< 4" \
        "coverage>=4.4.0,<4.6" \
        "flake8>=3,<4" \
        "black>=18,<19" \
        git+https://github.com/timothycrosley/isort@fcd80d4#egg=isort

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
