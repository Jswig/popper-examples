#!/usr/bin/env bash

cd docker

git clone --recursive https://github.com/Franko1307/slurm-docker-cluster.git

cd slurm-docker-cluster

docker build -t slurm-docker-cluster:17.02.10 .

docker-compose up -d

./register_cluster.sh

cd ..

docker cp . slurmctld:/data/

docker exec -e MACHINE=$MACHINE -e USERNAME=$USERNAME -it slurmctld ./data/docker-setup.sh


