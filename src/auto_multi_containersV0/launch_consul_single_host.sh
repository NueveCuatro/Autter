# docker-compose -f docker-compose-consul.yml stop
# docker network create consul-net
docker-compose -f docker-compose-consul-single-host.yml up 
#use dockr-compose -f docker-compose-single-host.yml down to shut the network down and completely remove the consul container