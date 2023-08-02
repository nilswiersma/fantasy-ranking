FROM python:3.8-alpine

# build tools
RUN apk update && apk add python3-dev gcc libc-dev git tree

ARG force_rebuild_from_here=1
RUN git clone https://github.com/nilswiersma/fantasy-ranking.git

WORKDIR /fantasy-ranking

RUN echo `ls -a /fantasy-ranking`
RUN echo `ls -a .`

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt
RUN pip install -e .

EXPOSE 8080

# ENTRYPOINT [ "waitress-serve", "--call", "flaskr:create_app" ]
ENTRYPOINT [ "python", "main.py" ]
