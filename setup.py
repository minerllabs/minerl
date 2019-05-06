import os
from os.path import isdir

import setuptools
from setuptools.command.develop import develop
from setuptools.command.install import install

with open("README.md", "r") as fh:
    markdown = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = fh.read()

malmo_branch="minerl"


# First download and build Malmo!
# We need to assert that Malmo is in the script directory. There HAS to be a better way to do this.

malmo_dir = os.path.join(os.path.dirname(__file__), 'minerl', 'env', 'Malmo')


def download(branch=malmo_branch, build=True, installdir=malmo_dir):
    """Download Malmo from github and build (by default) the Minecraft Mod.
    Args:
        branch: optional branch to clone. TODO Default is release version.
        build: build the Mod unless build arg is given as False.
        installdir: the install dir name. Defaults to MalmoPlatform.
    Returns:
        The path for the Malmo Minecraft mod.
    """
    # TODO: ADD VERSIONING BEFORE RELEASE !!!!!!!!!!!!!!!!!

    if branch is None:
        branch = malmo_branch

    # Check to see if the minerlENV is set up yet.
    if os.path.exists(malmo_dir):
        # TODO CHECK TO SEE IF THE VERSION MATCHES THE PYTHON VERSION!
        # TODO CHECKT OSEE THAT DECOMP WORKSPACE HAS BEEN SET UP (write a finished txt)

        cwd = os.getcwd()
        os.chdir(installdir)
        subprocess.check_call(["git", "pull"])
        os.chdir(cwd)
        return setup(build=build, installdir=installdir)

    # If it exists lets set up the env.
    # TODO: Convert to using loggers.
    print("❤️❤️❤️ Hello! Welcome to MineRL Env ❤️❤️❤️")
    print("MineRL is not yet setup for this package install! Downloading and installing Malmo backend.")

    try:
        subprocess.check_call(["git", "clone", "-b", branch, "https://github.com/cmu-rl/malmo.git", malmo_dir])
    except subprocess.CalledProcessError:
        print("ATTENTION: Setup failed! Was permission denied? "
              "If so you  installed the library using sudo (or a different user)."
              "Try rerunning the script as with sudo (or the user which you installed MineRL with).")

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
        # Optionally do a test build.
        if build:
            subprocess.check_call([gradlew, "setupDecompWorkspace", "build", "testClasses",
                                   "-x", "test", "--stacktrace", "-Pversion={}".format(malmo_version)])
        minecraft_dir = os.getcwd()
    finally:
        os.chdir(cwd)
    return minecraft_dir



def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        if not ".git" in path  and not "build" in path:
            paths.append((path, [os.path.join(path, f) for f in filenames if not isdir(f)]))
    return paths


data_files = []
data_files += package_files('minerl/env/missions')
data_files += package_files('minerl/env/Malmo')


setuptools.setup(
      name='minerl',
      version='0.0.8',
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
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: OS Independent",
            ],
    install_requires=requirements,
     data_files=data_files,
     include_package_data=True,
      )
