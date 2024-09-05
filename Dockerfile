FROM python:3.8-alpine

# build tools
RUN apk update && apk add python3-dev gcc libc-dev git tree

ADD https://github.com/nilswiersma/fantasy-ranking.git

WORKDIR /fantasy-ranking

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt
RUN pip install -e .

EXPOSE 8080

# ENTRYPOINT [ "waitress-serve", "--call", "flaskr:create_app" ]
ENTRYPOINT [ "python", "main.py" ]
