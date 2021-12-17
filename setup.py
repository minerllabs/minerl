# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import os

import subprocess
import pathlib
import setuptools
from setuptools import Command
from setuptools.command.install import install
from setuptools.command.install_lib import install_lib
from distutils.command.build import build

from setuptools.dist import Distribution
import shutil

with open("README.md", "r") as fh:
    markdown = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = fh.read()
with open("requirements-docs.txt", "r") as fh:
    requirements_docs = fh.read()

MALMO_BRANCH = "minerl"
MALMO_VERSION = "0.37.0"
MALMO_DIR = os.path.join(os.path.dirname(__file__), 'minerl', 'Malmo')
BINARIES_IGNORE = shutil.ignore_patterns(
    'build',
    'bin',
    'dists',
    'caches',
    'native',
    '.git',
    'doc',
    '*.lock',
    '.gradle',
    '.minecraftserver',
    '.minecraft')
# TODO: THIS IS NOT ACTUALLY IGNORING THE GRADLE.

# TODO: Potentially add locks to the binary ignores.


try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


    # @minecraft_build
    class bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            self.root_is_pure = False

except ImportError:
    bdist_wheel = None


# https://github.com/chinmayshah99/PyDP/commit/2ddbf849a749adad5d5db10d4d7e3479567087f3
# Bug here https://github.com/python/cpython/blob/28ab3ce92402d86aa400960d38f0d69f498bb677/Lib/distutils/command/install.py#L335
# Original fix proposed here: https://github.com/google/or-tools/issues/616
class BinaryDistribution(Distribution):
    """This class is needed in order to create OS specific wheels."""

    def has_ext_modules(self):
        return True


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class InstallPlatlib(install):
    def finalize_options(self):
        install.finalize_options(self)
        # Hmm so this is  wierd. When is has_ext_modules tru?
        if self.distribution.has_ext_modules():
            self.install_lib = self.install_platlib


class InstallWithMinecraftLib(install_lib):
    """Overrides the build command in install lib to build the minecraft library
    and place it in the build directory.
    """

    def build(self):
        super().build()
        # Install Minecraft to the build directory. Let's first print it.
        build_minecraft(MALMO_DIR, os.path.join(
            self.build_dir, 'minerl', 'Malmo'
        ))
        # TODO (R): Build the parser [not necessary at the moment]


class CustomBuild(build):
    def run(self):
        super().run()
        build_minecraft(MALMO_DIR, os.path.join(
            self.build_lib, 'minerl', 'Malmo'
        ))


class ShadowInplace(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        build_minecraft(MALMO_DIR, MALMO_DIR)


def build_minecraft(source_dir, build_dir):
    """Set up Minecraft for use with the MalmoEnv gym environment"""
    print("building Minecraft from  %s, build dir: %s" % (source_dir, build_dir))

    # 1. Copy the source dir to the build directory if they are not equivalent
    if source_dir != build_dir:
        print("copying source dir")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        shutil.copytree(source_dir, build_dir,
                        ignore=BINARIES_IGNORE
                        )

    gradlew = 'gradlew.bat' if os.name == 'nt' else './gradlew'

    # TODO: Remove the change directoty.
    # 2. Change to the directory and build it; perhaps it need live inside of MineRL
    cwd = os.getcwd()
    # change to join of build dir and 'Minecraft'
    os.chdir(os.path.join(build_dir, 'Minecraft'))
    try:
        # Create the version properties file.
        pathlib.Path("src/main/resources/version.properties").write_text("malmomod.version={}\n".format(MALMO_VERSION))
        minecraft_dir = os.getcwd()
        print("CALLING SETUP.")
        os.environ['GRADLE_USER_HOME'] = os.path.join(minecraft_dir, 'run')
        subprocess.check_call('{} -g run/gradle shadowJar'.format(gradlew).split(' '))

        # Now delete all the *.lock files recursively  in the Minecraft_dir. Should be platform agnostic.
        for root, dirs, files in os.walk(minecraft_dir):
            for lockfile in files:
                if lockfile.endswith('.lock'):
                    print("Deleting %s" % (lockfile))
                    os.remove(os.path.join(root, lockfile))
    finally:
        os.chdir(cwd)
    return build_dir


# Don't build binaries (requires Java) on readthedocs.io server.
if os.environ.get("READTHEDOCS"):
    cmdclass = {}
else:
    cmdclass = {
        'bdist_wheel': bdist_wheel,
        'install': InstallPlatlib,
        'install_lib': InstallWithMinecraftLib,
        'build_malmo': CustomBuild,
        'shadow_develop': ShadowInplace,
    }


setuptools.setup(
    name='minerl',
    # TODO(shwang): Load from minerl.version.VERSION or something so we don't have to update
    # multiple version strings.
    version=os.environ.get('MINERL_BUILD_VERSION', '0.4.4'),
    description='MineRL environment and data loader for reinforcement learning from human demonstration in Minecraft',
    long_description=markdown,
    long_description_content_type="text/markdown",
    url='http://github.com/minerllabs/minerl',
    author='MineRL Labs',
    author_email='minerl@andrew.cmu.edu',
    license='MIT',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    extras_require={"docs": requirements_docs},
    distclass=BinaryDistribution,
    include_package_data=True,
    cmdclass=cmdclass,
    data_files=['requirements-docs.txt'],
)

# global-exclude .git/*
# global-exclude  build/ bin/ dists/ caches/  native/ doc/ *.lock 
# global-exclude  *.gradle/* *.minecraft/ *.minecraftserver/
# global-exclude  *.fuse_hidden*
