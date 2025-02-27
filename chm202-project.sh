#!/bin/bash
#
echo "Setting up spack for chm202 project on frontier:"

PROJECT_PATH=/lustre/orion/chm202/proj-shared
export SPACK_USER_CONFIG_PATH=$PROJECT_PATH/apps/.spack
source $PROJECT_PATH/spack/share/spack/setup-env.sh


spack load /jpuppf6k

echo "cp2k is loaded now. You can use cp2k with cp2k.psmp"
echo "source this file in your batch jobs."

echo "The README.md in the project_shared directory contains all information to run cp2k on"
echo "frontier."
