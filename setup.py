from setuptools import setup
import os

if __name__ == "__main__":
    setup(name='esper-video',
          version='0.1.0',
          description='A framework for end-to-end video analytics',
          url='http://github.com/scanner-research/esper',
          author='Will Crichton',
          author_email='wcrichto@cs.stanford.edu',
          license='Apache 2.0',
          entry_points={'console_scripts': ['esper=esper.configure:main']},
          install_requires=['docker-compose', 'pyyaml', 'toml', 'dotmap'],
          include_package_data=True,
          packages=['esper'],
          zip_safe=False)
