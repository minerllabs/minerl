import os
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

    # If it exists lets set up the env.
    # TODO: Convert to using loggers.
    #print("<3 <3  Hello! Welcome to MineRL Env <3 <3")
    #print("MineRL is not yet setup for this package install! Downloading and installing Malmo backend.")

    #try:
    #    subprocess.check_call(["git", "clone", "-b", branch, "https://github.com/cmu-rl/malmo.git", malmo_dir])
    #except subprocess.CalledProcessError:
    #    print("ATTENTION: Setup failed! Was permission denied? "
    #          "If so you  installed the library using sudo (or a different user)."
    #          "Try rerunning the script as with sudo (or the user which you installed MineRL with).")
    #

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
        # Optionally do a test build.
        if build:
            subprocess.check_call([gradlew, "setupDecompWorkspace", "build", "testClasses",
                                   "-x", "test", "--stacktrace", "-Pversion={}".format(malmo_version)])
        minecraft_dir = os.getcwd()
    finally:
        os.chdir(cwd)
    return minecraft_dir


download()

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):

        # if not ("Malmo/Malmo" in path): print(path)
        if (
            not ".git" in path 
            and not "build" in path 
            and not "Malmo/Malmo" in path
            and not ".minecraft" in path
            and not ".minecraftserver" in path
            and not "Malmo/doc" in path
            and not "Malmo/test" in path
            and not "Malmo/MalmoEnv" in path
            and not "Malmo/ALE_ROMS" in path):
            print(path)
            paths.append((path, [os.path.join(path, f) for f in filenames if not isdir(f)]))
    # 1/0
    return paths


data_files = []
data_files += package_files('minerl/env/missions')
data_files += package_files('minerl/env/Malmo')


setuptools.setup(
      name='minerl',
      version='0.1.9',
      description='MineRL environment and data loader for reinforcement learning from human demonstration in Minecraft',
      long_description=markdown,
      long_description_content_type="text/markdown",
      url='http://github.com/minenetproject/minerl',
      author='MineRL Labs',
      author_email='minerl@andrew.cmu.edu',
      license='MIT',
      packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
            classifiers=[
                 "Programming Language :: Python :: 3",
                 "Operating System :: OS Independent",
            ],
    install_requires=requirements,
     data_files=data_files,
     include_package_data=True,
      )
