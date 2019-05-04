import os
from os.path import isdir

import setuptools
from setuptools.command.develop import develop
from setuptools.command.install import install

with open("README.md", "r") as fh:
      markdown = fh.read()
with open("requirements.txt", "r") as fh:
      requirements = fh.read()


# First download and build Malmo!
# We need to assert that Malmo is in the script directory. There HAS to be a better way to do this.
from minerl.env.bootstrap import download
download()

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
          paths.append((path, [os.path.join(path, f) for f in filenames if  not isdir(f)]))
    return paths

data_files = []
data_files += package_files('minerl/env/missions')
data_files += package_files('minerl/env/Malmo')


setuptools.setup(
      name='minerl',
      version='0.0.4',
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
