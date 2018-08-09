#!/usr/bin/env bash

sinfo

scp -r ./ $USERNAME@$MACHINE:

ssh $USERNAME@$MACHINE sbatch job.sh
