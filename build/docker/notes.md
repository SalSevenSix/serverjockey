# Docker and Ptero Build Notes


## Links
* https://devopscube.com/build-docker-image/
* https://www.techrepublic.com/article/how-to-create-a-docker-image-and-push-it-to-docker-hub/
* Setup https://pterodactyl.io/panel/1.0/getting_started.html
* Ubuntu container for pterodactyl https://github.com/parkervcp/yolks/tree/master/steamcmd


## Common Commands
```
docker images
docker rmi <image>:<tag>
docker ps --all
docker rm <container>
docker system prune

docker build --no-cache -t <image>:<tag> .
docker commit -m "<comment>" -a "Bowden Salis <bsalis76@gmail.com>" <container> salsevensix/<image>:<tag>
docker commit -m "Release 0.5.0" -a "Bowden Salis <bsalis76@gmail.com>" 37968a3761cc salsevensix/serverjockey:0.5.0

docker login
docker push salsevensix/<image>:<tag>
docker run --ulimit memlock=8589934592:8589934592 -p 6164:6164/tcp <image>:<tag>
docker start -a <container>
docker stop <container>
docker exec -it <container> bash
```
