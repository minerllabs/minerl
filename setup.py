# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import os
import sys
import json
from os.path import isdir

import subprocess
import pathlib
import setuptools
from setuptools import Command
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.install_lib import install_lib
from distutils.command.build import build

from setuptools.dist import Distribution
import shutil

with open("README.md", "r") as fh:
    markdown = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = fh.read()

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

def unpack_assets():
    asset_dir = os.path.join(os.path.expanduser('~'), '.gradle', 'caches', 'forge_gradle', 'assets')
    output_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'minerl', 'MCP-Reborn', 'src', 'main', 'resources')
    index = load_asset_index(os.path.join(asset_dir, 'indexes', '1.16.json'))
    unpack_assets_impl(index, asset_dir, output_dir)

def load_asset_index(index_file):
    with open(index_file) as f:
        return json.load(f)

def unpack_assets_impl(index, asset_dir, output_dir):
    for k, v in index['objects'].items():
        asset_hash = v["hash"]
        src = os.path.join(asset_dir, 'objects', asset_hash[:2], asset_hash)
        dst = os.path.join(output_dir, k)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)

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

class CustomBuild(build):
    def run(self):
        super().run()


class ShadowInplace(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pass

def prep_mcp():
    mydir = os.path.abspath(os.path.dirname(__file__))

    # First, get MCP and patch it with our source.
    if os.name == 'nt':
        # Windows is picky about this, too... If you have WSL, you have
        # bash command, but an absolute path won't work. So lets instead
        # use relative paths
        old_dir = os.getcwd()
        os.chdir(os.path.join(mydir, 'scripts'))

        try:
            subprocess.check_call(['bash.exe', 'setup_mcp.sh'])
            subprocess.check_call(['bash.exe', 'patch_mcp.sh'])
        except Exception as e:
            raise RuntimeError(
                "\n\n`bash` command not found. You have at least two options to fix this:"
                " 1. Install Windows Subsystem for Linux (WSL. Tested on WSL 2)."
                " 2. Install bash along some other tools. E.g., git will come with bash: https://git-scm.com/downloads ."
                "    After installation, you may have to update environment variables to include a path which contains"
                "    'bash.exe'. For above git tools, this is [installation-dir]/bin."
                "After installation, you should have 'bash' command in your command line/powershell.\n\n"
            )

        os.chdir(old_dir)
    else:
        subprocess.check_call(['bash', os.path.join(mydir, 'scripts', 'setup_mcp.sh')])
        subprocess.check_call(['bash', os.path.join(mydir, 'scripts', 'patch_mcp.sh')])

    # Next, move onto building the MCP source
    gradlew = 'gradlew.bat' if os.name == 'nt' else './gradlew'
    workdir = os.path.join(mydir, 'minerl', 'MCP-Reborn')
    if os.name == 'nt':
        # Windows is picky about being in the right directory to run gradle
        old_dir = os.getcwd()
        os.chdir(workdir)
    subprocess.check_call('{} downloadAssets'.format(gradlew).split(' '), cwd=workdir)
    unpack_assets()
    subprocess.check_call('{} clean build shadowJar'.format(gradlew).split(' '), cwd=workdir)
    if os.name == 'nt':
        os.chdir(old_dir)


prep_mcp()
setuptools.setup(
    name='minerl',
    version=os.environ.get('MINERL_BUILD_VERSION', '1.0.0'),
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
    distclass=BinaryDistribution,
    include_package_data=True,
    cmdclass={
        'bdist_wheel': bdist_wheel,
        'install': InstallPlatlib,
        'install_lib': InstallWithMinecraftLib,
        'build_malmo': CustomBuild,
        'shadow_develop': ShadowInplace},
)
