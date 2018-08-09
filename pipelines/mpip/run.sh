#!/bin/bash
set -ex

docker exec -it -e MACHINE=$MACHINE -e USERNAME=$USERNAME slurmctld ./data/docker-run.sh

