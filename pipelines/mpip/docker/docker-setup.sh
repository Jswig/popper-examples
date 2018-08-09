#!/usr/bin/env bash

cd data/scripts

yum groupinstall -y  "Development Tools"
yum install -y gcc-gfortran
yum -y install gcc

source .common.sh

yum install -y patch
# yum group install -y "Development Tools"

find_or_install_spack

# installs dependencies of the experiment using Spack
# TODO install architecture-specific versions

spack install openmpi@2.0.1
spack install lulesh
spack install mpip

