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

There is an issue with cp2k when more than one MPI rank are assigned to a single GPU and this configuration should be avoided until we figure out with AMD where the problem resides. 

## Using CP2K on frontier

I compiled one version of CP2K `jpuppf6ks` for `cp2k`. `dlaf-f` is not included in the build for the time being as the build crashes and performances are still not good. The reasons for the crash are known and will be fixed in the near future. 

```[bash]
source  /lustre/orion/chm202/proj-shared/chm202-project.sh
spack load /jpuppf6k
```
CP2K should be available using the command line `cp2k.psmp`.

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

# this line is needed because I compiled cp2k withlink to this library but the default one is older.

# this is needed because libfabric default is version 1.15. 
module load libfabric/1.22.0

# default: we load cp2k without dla-f for the time being until I figure out with dla-f team why one cp2k-dlaf test fails
spack load /jpuppf6k

# it is not needed in practice but I indicate it for reference
CP2K_ROOT="/lustre/orion/chm202/proj-shared/apps/linux-sles15-zen3/gcc-13.3.0/cp2k-master-jpuppf6ksjgzc7mi2bg3ymymuvswx7rc"
# two options either call ${CP2K_ROOT}/bin/cp2k.psmp or directly call cp2k.psmp

# the command line is !!!!! CP2K WITHOUT DLAF
srun --gpus-per-task=1 --gpu-bind=closest ${CP2K_ROOT}/bin/cp2k.psmp -i my_input.inp -o my_input.out
```

Of course the runtime parameters `-N`, `-t` `-n`, etc should be adapted to the specific simulation.

## where to get help
send me an email at `tmathieu@ethz.ch` directly if you have any problem. I will try to reply as fast as I can. 

## spack configuration for frontier
The repository also contains the necessary files for configuring spack. The configuration is not perfect as it does not include yet GPU direct support for instance but it should be fixed in the near future. All configurations files can be found in the spack directory. Copy the `packages.yaml` and `config.yaml` to any desired location and then modify the script `chm202-project.sh` accordingly. The file `config.yaml` also need to be modified, this line in particular

```[python]
  # This is the path to the root of the Spack install tree.
  # You can use $spack here to refer to the root of the spack instance.
  install_tree:
    root: /lustre/orion/chm202/proj-shared/apps
```

It is also strongly advised to run the two following commands the first time spack is used 

```[bash]
module load PrgEnv-gnu
```

This will ensure that gcc 13.3 is found. One may add an extra `module load gcc-native/12.3` is another compiler is needed.

Compiling cp2k can achieved with the command line

```[bash]
spack install "cp2k@master%gcc@13.3+rocm+spla+spglib+libint+libxc+cosma+sirius+libvori+pw_gpu+dftd4+smeagol+openmp+hdf5 build_system=cmake smm=libxsmm ^[virtuals=blas,lapack,scalapack] intel-oneapi-mkl@2023+cluster+gfortran+shared threads=openmp ^mpich@3.4 ^sirius@develop+rocm+scalapack+pugixml+fortran+openmp+vdwxc ^spla+rocm ^gsl+pic+shared ^hipfft@6.3.1 ^hipblas@6.3.1 ^rocblas@6.3.1 ^rocfft@6.3.1 ^umpire%gcc ^hip@6.3.1 ^rocsolver@6.3.1 ^libxc@7.0.0 ^hdf5+fortran+shared+hl"
```
Removing the double quote will most likely result in strange error messages from spack. It is particularly true when zsh is used as shell. So it is advised to quote the spack specification string. running this command line will takes several minutes or few hours at worst. 

Running 
```[bash]
spack find -l
```
should return all intalled packages. Running `spack load cp2k` should make cp2k available. 



## Running the regtests

Only if you absolutely want to test everything. In general nothing is merged in cp2k github repo if it breaks any of the regtests. I paid special attention to run them and if any member of the team wants to use an updated version; it is probably better I run all these steps for them. Every member also has the option to compile cp2k by hand but i would not recommend it as am initial step. I will provide as much help as I can with the build process. 



```[bash]
#!/bin/bash

#SBATCH -N 4
#SBATCH -A chm202
#SBATCH -t 1:00:00

source /lustre/orion/chm202/proj-shared/chm202-project.sh
module load miniforge3
spack load /jpuppf6

# root where cp2k is installed, or cp2k root source code
CP2K_ROOT="/lustre/orion/chm202/proj-shared/apps/linux-sles15-zen3/gcc-13.2.1/cp2k-master-jpuppf6ksjgzc7mi2bg3ymymuvswx7rc"

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
