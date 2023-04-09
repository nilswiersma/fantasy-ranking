docker build -t flaskr .

docker run \
    -p 8080:8080 \
    --mount type=bind,source="$(pwd)"/data,target=/data \
    flaskr
