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
- dftd4
- sirius
- libvori
- libbqb
- offload_hip
- spla_gemm_offloading
- libvdwxc
- hdf5
- libsmeagol
- ROCM 6.3.1
- spla

# Known issues
- From internal testing on AMD machines, we found that running cp2k with more than
one MPI rank per GPU can lead to wrong results. AMD is suggesting that the issue
is related to the HPE environment itself which is possible. 
- The first cp2k spack installation referenced `/jpuppf6ks` has a bug that
  affects molecular dynamics. It is a memory leak in the grid backend that was
  introduced almost two years ago but never found until Ada reported a crash
  during MD simulations. This issue does **NOT** affect the results. All single
  points calculations are numerically correct. More importantly, the bug is
  fixed and a new version of `cp2k` is available on Frontier. The MD simulations
  were tested using the H2O benchmarks with a memory check tool to ensure that
  the problem was not present anymore. The `chm202-project.sh` was modified to
  reflect these changes. 
  
## Using CP2K on frontier

The current recommended version of `CP2K` is tagged `/godu5pw`. Your script
should contain these lines (the comments can be removed) before calling cp2k.

```[bash]
source  /lustre/orion/chm202/proj-shared/chm202-project.sh

# The first version of CP2K is still available for reproducible reasions
# spack load /jpuppf6ks
#
spack load /godu5pw
```
CP2K should be available using the command line `cp2k.psmp`.

## Typical batch script

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
spack load /godu5pw

# it is not needed in practice but I indicate it for reference
CP2K_ROOT="/lustre/orion/chm202/proj-shared/apps/linux-sles15-zen3/gcc-13.3.0/cp2k-master-godu5pwsq2spbkskyemoybp5fs4lj4yq"
# two options either call ${CP2K_ROOT}/bin/cp2k.psmp or directly call cp2k.psmp

# the command line is !!!!! CP2K WITHOUT DLAF
srun --gpus-per-task=1 --gpu-bind=closest ${CP2K_ROOT}/bin/cp2k.psmp -i my_input.inp -o my_input.out
```

Of course the runtime parameters `-N`, `-t` `-n`, etc should be adapted to the specific simulation.

## Where to get help
send me an email at `tmathieu@ethz.ch` directly if you have any problem. I will
try to reply as fast as I can.

## Compiling CP2K yourselves

The CP2K source code can be found in the following directory:
`/lustre/orion/chm202/proj-shared/codes/cp2k`. CP2K can be compiled with the
following commands

```[bash]
# load CP2K and all its dependencies
spack load /godu5pw
spack load cmake@3.31.6
module load ninja
module unload cray-libsci

cd /lustre/orion/chm202/proj-shared/codes/cp2k
mkdir build-test
cd build-test
cmake -DCP2K_USE_ELPA=NO -DCP2K_USE_DLAF=NO -DCP2K_USE_DEEPMD=NO -DCP2K_USE_PLUMED=NO -DCP2K_USE_LIBTORCH=NO -DCP2K_BLAS_VENDOR=MKL -DCP2K_SCALAPACK_VENDOR=MKL -DCP2K_USE_ACCEL=hip -DCP2K_WITH_GPU=Mi250 -GNinja -DCMAKE_INSTALL_PREFIX=myprettypath -DCMAKE_BUILD_SHARED=NO ..
ninja -j8
ninja install
```

then the `PATH` and `LD_LIBRARY_PATH` variables should be set accordingly. 'myprettypath' is the installation directory. 

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

Only if you absolutely want to test everything. In general nothing is merged in
cp2k github repo if it breaks any of the regtests. I paid special attention to
run them and if any member of the team wants to use an updated version; it is
probably better I run all these steps for them. Every member also has the option
to compile cp2k by hand but i would not recommend it as am initial step. I will
provide as much help as I can with the build process.



```[bash]
#!/bin/bash

#SBATCH -N 4
#SBATCH -A chm202
#SBATCH -t 1:00:00

source /lustre/orion/chm202/proj-shared/chm202-project.sh
module load miniforge3
spack load /godu5pw

# set CP2K_DATA_DIR variable if you compile cp2k by hand. Do **not** set it when CP2K is compiled with spack
# export CP2K_DATA_DIR=${CP2K_ROOT}/data

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

# CP2K source code is available here
cd /lustre/orion/chm202/proj-shared/codes/cp2k
# some tests are indicated as failed but they are not in practice. mpi io and cp2k do not seem to play nice some time

python3.10 ./regtests-dask.py --input-dir /lustre/orion/chm202/proj-shared/codes/cp2k --executable "srun -u -N 1 -n 2 -c 4 --gpus-per-task=1 --gpu-bind=closest cp2k.psmp \$input_file" --scheduler-file scheduler.json
```
and the `regtests-dask.py` script.
