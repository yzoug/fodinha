# Use the Python3.8.2 image based on alpine
FROM python:3.8.2-alpine

# Set the working directory to /app
WORKDIR /deploy

# Copy the current directory contents into the container at /app 
ADD . /deploy

# install c compiler and build tools
# https://github.com/gliderlabs/docker-alpine/issues/158
RUN apk add build-base linux-headers pcre-dev

# Install the dependencies
RUN pip install -r requirements.txt

# run the command to start uWSGI
CMD ["uwsgi", "uwsgi-local.ini"]

