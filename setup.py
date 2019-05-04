import setuptools

with open("README.md", "r") as fh:
      markdown = fh.read()
with open("requirements.txt", "r") as fh:
      requirements = fh.read()
setuptools.setup(
      name='minerl',
      version='0.0.2',
      description='MineRL environment and data loader for reinforcement learning from human demonstration in Minecraft',
      long_description=markdown,
      long_description_content_type="text/markdown",
      url='http://github.com/minenetproject/minerl',
      author='MineRL Labs',
      author_email='minerl@andrew.cmu.edu',
      license='MIT',
      packages=setuptools.find_packages(),
            classifiers=[
                 "Programming Language :: Python :: 3",
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: OS Independent",
            ],
      install_requires=requirements,
      )