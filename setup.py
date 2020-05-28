from setuptools import setup
import sys
import os
from os.path import isdir

import setuptools
import subprocess

from distutils.command.build import build

merge_src = os.path.join(os.path.dirname(__file__), "minerl_data", "pipeline", "parser")
assets = os.path.join(os.path.dirname(__file__), "minerl_data", "assets")


class Build(build):
    """Customized setuptools build command - builds protos on build."""

    def run(self):
        protoc_command = ["make"]
        if subprocess.call(protoc_command, cwd=os.path.join(
                merge_src
        )) != 0:
            sys.exit(-1)
        print("sup")
        super().run()


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):

        # if not ("Malmo/Malmo" in path): print(path)
        if (
                not ".git" in path
        ):
            paths.append((path, [os.path.join(path, f) for f in filenames if not isdir(f) and (
                not f == "parse"
            )]))
    print(paths)
    return paths


setup(
    name="minerl_data",
    version='0.0.1',
    packages=setuptools.find_packages(),
    author="William Guss, Brandon Houghton",
    cmdclass={
        'build': Build,
    },
    data_files=package_files(merge_src),
)
