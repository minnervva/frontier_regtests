#!/bin/bash

#SBATCH -N 4
#SBATCH -A chm202
#SBATCH -t 1:00:00

source /lustre/orion/chm202/proj-shared/chm202-project.sh
module load miniforge3

# root where cp2k is installed, or cp2k root source code
CP2K_ROOT="/lustre/orion/chm202/proj-shared/apps/linux-sles15-zen3/gcc-13.2.1/cp2k-master-clpc3biqqyyvjipol7sn7roerz5izu6b"

# set CP2K_DATA_DIR variable, redundant when cp2k is compiled with spack
export CP2K_DATA_DIR=${CP2K_ROOT}/data

# launch the dask scheduler
~/.local/23.11.0-0/bin/dask-scheduler --no-show --scheduler-file scheduler.json > dask-scheduler.out 2>&1 &
sleep 5

# launch the workers
for((i=0;i<16;i++)); do
~/.local/23.11.0-0/bin/dask-worker --nthreads 1 --nworkers 1 --scheduler-file scheduler.json > dask-worker$i.out 2>&1 &
done
sleep 5

# small trick to make mkl believe it runs with intel cpu

cat << EOF > ${CP2K_ROOT}/libfakeintel.c
int mkl_serv_intel_cpu_true() {
  return 1;
}
EOF

gcc -shared -fPIC -o libfakeintel.so libfakeintel.c


LD_PRELOAD=${CP2K_ROOT}/libfakeintel.so


cd /lustre/orion/chm202/proj-shared/codes/cp2k
python3.10 ./regtests-dask.py --input-dir /lustre/orion/chm202/proj-shared/codes/cp2k --executable "srun -u -N 1 -n 2 -c 4 --gpus-per-task=1 --gpu-bind=closest ${CP2K_ROOT}/bin/cp2k.psmp \$input_file" --scheduler-file scheduler.json
