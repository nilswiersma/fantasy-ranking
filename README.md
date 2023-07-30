clear all containers:
docker rm -vf $(docker ps -a -q)

clear all images:
docker rmi -f $(docker images -a -q)

docker build -t flaskr .

docker run \
    -p 80:8080 \
    --mount type=bind,source="$(pwd)"/data,target=/fantasy-ranking/data \
    flaskr


https://www.kryogenix.org/code/browser/sorttable/sorttable.js