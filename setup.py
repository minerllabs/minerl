import os
import sys
from os.path import isdir

import subprocess
import pathlib
import setuptools
from setuptools.command.develop import develop
from setuptools.command.install import install

with open("README.md", "r") as fh:
    markdown = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = fh.read()

malmo_branch="minerl"
malmo_version="0.37.0"

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
    class bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            self.root_is_pure = False
except ImportError:
    bdist_wheel = None

# First download and build Malmo!
# We need to assert that Malmo is in the script directory. There HAS to be a better way to do this.

malmo_dir = os.path.join(os.path.dirname(__file__), 'minerl', 'env', 'Malmo')

def download(branch=malmo_branch, build=False, installdir=malmo_dir):
    """Download Malmo from github and build (by default) the Minecraft Mod.
    Args:
        branch: optional branch to clone. TODO Default is release version.
        build: build the Mod unless build arg is given as False.
        installdir: the install dir name. Defaults to MalmoPlatform.
    Returns:
        The path for the Malmo Minecraft mod.
    """
    if branch is None:
        branch = malmo_branch

    # Check to see if the minerlENV is set up yet.
    assert os.path.exists(os.path.join(malmo_dir, 'Minecraft')), "Did you initialize the submodules."
    build = build or not os.path.exists(os.path.join(malmo_dir, 'Minecraft', 'build'))
    return setup(build=build, installdir=installdir)

def setup(build=True, installdir=malmo_dir):
    """Set up Minecraft for use with the MalmoEnv gym environment"""

    gradlew = './gradlew'
    if os.name == 'nt':
        gradlew = 'gradlew.bat'

    cwd = os.getcwd()
    os.chdir(installdir)
    os.chdir("Minecraft")
    try:
        # Create the version properties file.
        pathlib.Path("src/main/resources/version.properties").write_text("malmomod.version={}\n".format(malmo_version))
        minecraft_dir = os.getcwd()
        subprocess.check_call('./gradlew -g run/gradle shadowJar'.split(' '))
    finally:
        os.chdir(cwd)
    return minecraft_dir

download()

setuptools.setup(
      name='minerl',
      version=os.environ.get('MINERL_BUILD_VERSION', '0.2.9'),
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
      include_package_data=True,
      cmdclass={'bdist_wheel': bdist_wheel},
)
