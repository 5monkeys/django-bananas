FROM python:3

# Install system dependencies
RUN apt-get update && apt-get install -y \
        gettext && \
    pip install Django

# Install bananas source
WORKDIR /usr/src
COPY . django-bananas
RUN pip install -e django-bananas && \
    rm -rf /usr/src/django-bananas/example && \
    mkdir /app
    
# Install example app
WORKDIR /app
COPY example ./

ENTRYPOINT ["python3", "manage.py"]
