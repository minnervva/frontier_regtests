# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems import cmake, meson
from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.meson import MesonPackage

from spack.package import *


class Multicharge(CMakePackage, MesonPackage):
    """Electronegativity equilibration model for atomic partial charges"""

    homepage = "https://github.com/grimme-lab/multicharge"
    url = "https://github.com/grimme-lab/multicharge/releases/download/v0.0.0/multicharge-0.0.0.tar.xz"
    git = "https://github.com/grimme-lab/multicharge.git"

    maintainers("RMeli", "awvwgk")

    license("Apache-2.0", checked_by="RMeli")

    build_system("cmake", "meson", default="meson")

    version("main", branch="main")
    version("0.4.0", sha256="16aea6d8ba2f81ced3de1153cb3d73083aa7ca43c3b2b6ee9799127bab5d60d1")
    version("0.3.1", sha256="180541714c26804a2d66edd892c8cd4cb40a21acbaf7edb24aaf04d580368b97")
    version("0.3.1", sha256="180541714c26804a2d66edd892c8cd4cb40a21acbaf7edb24aaf04d580368b97")
    version("0.3.0", sha256="e8f6615d445264798b12d2854e25c93938373dc149bb79e6eddd23fc4309749d")

    variant("openmp", default=True, description="Enable OpenMP support")

    depends_on("c", type="build")
    depends_on("fortran", type="build")
    depends_on("lapack")
    depends_on("mctc-lib build_system=cmake", when="build_system=cmake")
    depends_on("mctc-lib build_system=meson", when="build_system=meson")
    depends_on("mctc-lib@0.4.0:", when="@0.4.0:")
    depends_on("mctc-lib@0.3:0.4", when="@0.3:")

    def url_for_version(self, version):
        if self.spec.satisfies("@:0.3.0"):
            return f"https://github.com/grimme-lab/multicharge/releases/download/v{version}/multicharge-{version}.tar.xz"
        else:
            return f"https://github.com/grimme-lab/multicharge/releases/download/v{version}/multicharge-{version}-source.tar.xz"


class CMakeBuilder(cmake.CMakeBuilder):
    def cmake_args(self):
        args = [self.define_from_variant("WITH_OpenMP", "openmp")]
        return args


class MesonBuilder(meson.MesonBuilder):
    def meson_args(self):
        lapack = self.spec["lapack"].libs.names[0]
        if lapack == "lapack":
            lapack = "netlib"
        elif lapack.startswith("mkl"):
            lapack = "mkl"
        elif lapack != "openblas":
            lapack = "auto"

        return [
            "-Dopenmp={0}".format(str("+openmp" in self.spec).lower()),
            "-Dlapack={0}".format(lapack),
        ]
