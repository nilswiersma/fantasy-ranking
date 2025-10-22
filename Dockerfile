FROM python:3-alpine

# build tools
RUN apk update && apk add python3-dev gcc libc-dev git tree build-base

COPY . /fantasy-ranking/

WORKDIR /fantasy-ranking

# install the dependencies and packages in the requirements file
RUN pip install -e .

EXPOSE 8080

# ENTRYPOINT [ "waitress-serve", "--call", "flaskr:create_app" ]
ENTRYPOINT [ "python", "-m", "fantasy_ranking" ]
