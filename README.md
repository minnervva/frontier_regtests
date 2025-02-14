# Introduction

This short readme contains necessary information to run cp2k on Frontier. The latest version of CP2K (as of Feb. 10th 2025) was compiled with spack. The following dependencies are enabled

- omp
- libint
- fftw3
- fftw3_mkl
- libxc
- parallel
- scalapack
- cosma
- xsmm
- dbcsr_acc
- spglib
- mkl
- libdftd4
- sirius
- libvori
- libbqb
- offload_hip
- spla_gemm_offloading
- libvdwxc
- hdf5
- libsmeagol
- ROCM 6.3.1
- grpp (depending)
- dla-f (present but one regtest fails)

There is an issue with cp2k when more than one MPI rank are assigned to a single GPU and this configuration should be avoided until we figure out with AMD where the problem resides. 

## Using CP2K on frontier

I compiled two versions of CP2K `clpc3biqq` for `cp2k` without `dla-f` and 
`7duvxma` for `cp2k` with `dla-f`. The strange string hashes that tell `spack` which version to load (like `module load`). The only function needed from spack is load. To run it add the following in your batch script.

```[bash]
source  /lustre/orion/chm202/proj-shared/chm202-project.sh
spack load /clpc3biqq
```
It will load the version of `cp2k` without `dla-f`. If `dla-f` is needed then change `/clpc3biqq` with `/7duvxma`. Note you will have to change the CP2K input file as I am not sure that dla-f is the default eigensolver. 

## typical batch script

The following script can be used as a starting point for batch jobs

```[bash]
#!/bin/bash

#SBATCH -N 4
#SBATCH -A chm202
#SBATCH -t 2:00:00
#SBATCH -n 32 # number of tasks (1 task per GPU * 8 * number of nodes)
#SBATCH -c 4 # OMP threads

source /lustre/orion/chm202/proj-shared/chm202-project.sh
spack load /clpc3biqq

CP2K_ROOT="/lustre/orion/chm202/proj-shared/apps/linux-sles15-zen3/gcc-13.2.1/cp2k-master-clpc3biqqyyvjipol7sn7roerz5izu6b"

# two options either call ${CP2K_ROOT}/bin/cp2k.psmp or directly call cp2k.psmp

# the command line is

srun --gpus-per-task=1 --gpu-bind=closest ${CP2K_ROOT}/bin/cp2k.psmp -i my_input.inp -o my_input.out
```

Of course the runtime parameters `-N`, `-t` `-n`, etc should be adapted to the specific simulation.

## where to get help
send me an email at `tmathieu@ethz.ch` directly if you have any problem. I will try to reply as fast as I can. 

## Next update

Frontier has a short maintenance window on Feb. 18th with a new version of libfabric that fixes a performance bug. I will recompile CP2K and run the regtests with the new version after the update. The regtests python script and batch script will be available on minnerva github. 

## Running the regtests

Ideally, all the regtests should be ran every time cp2k is recompiled. These two scripts should help with this. `dask` distributed is also needed as the regtests script is based on dask for managing the different tests. CP2K source code is needed whatever the way CP2K is compiled as the regtests are not part of `CP2K` installation. There are two options at that stage, compile `cp2k` manually or better use `spack`.
In practice, the only binary needed is `cp2k.psmp` (the unit tests are still missing) to run the tests. If compiled by hand then the environment variable `CP2K_DATA_DIR` should initialized to the path where CP2K pp data are located. 

If cp2k is compiled with spack then, the easiest is to load the newly compiled version of cp2k with spack (`spack load \xyz`) and then use this script

```[bash]
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
```
and the `regtests-dask.py` script.
