import os
from setuptools import setup

requirements = []
if os.path.isfile('requirements.txt'):
    with open('requirements.txt') as f:
        requirements = f.read().splitlines()

setup(name='cutils',
      version='0.1',
      description='A collection of useful functions for crawling in Python',
      url='',
      download_url='git+https://github.com/lengors/cutils.git#egg=cutils',
      author='Pedro Cavadas',
      author_email='pedro.cavadas.1998@outlook.com',
      license='The Unlicense',
      packages=['cutils'],
      zip_safe=False,
      install_requires=requirements)
