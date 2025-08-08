# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems import cmake, meson
from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.meson import MesonPackage

from spack.package import *


class Jonquil(MesonPackage, CMakePackage):
    """Bringing TOML blooms to JSON land"""

    homepage = "https://toml-f.readthedocs.io/en/latest/how-to/jonquil/"
    url = "https://github.com/toml-f/jonquil/releases/download/v0.3.0/jonquil-0.3.0.tar.xz"
    git = "https://github.com/toml-f/jonquil/"

    maintainers("mtaillefumier")

    license("Apache-2.0")

    build_system("cmake", "meson", default="meson")

    version("main", branch="main")
    version("0.3.0", sha256="4bc3f0ae47ac2e009a0dc733ad9d0f16db4dfed13b50f58b9a06bb3a579eec47")
    version("0.2.0", sha256="68448be7f399942e15a05ed7a149cc226a8ee81a8ce66cd68a2d01d9fc86527e")
    version("0.1.0", sha256="0c8854da047306cad357143fe56f7afe3d323d89aa7383b6614b2b587f580044")

    depends_on("fortran", type="build")
    depends_on("meson@0.57.2:", type="build", when="build_system=meson")

    depends_on("toml-f")
    depends_on("pkgconfig", type="build")


class CMakeBuilder(cmake.CMakeBuilder):
    def cmake_args(self):
        return []


class MesonBuilder(meson.MesonBuilder):
    def meson_args(self):
        return []
