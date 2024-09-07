# docker

clear all containers:
```
docker rm -vf $(docker ps -a -q)
```

clear all images:
```
docker rmi -f $(docker images -a -q)
```

```
docker build -t fantasy-ranking .
```

```
docker run \
    --rm \
    -p 8081:8080 \
    --mount type=bind,source="$(pwd)"/data,target=/fantasy-ranking/data \
    fantasy-ranking
```

# local test

flask --app flaskr run --debug

# links

https://www.kryogenix.org/code/browser/sorttable/sorttable.js
