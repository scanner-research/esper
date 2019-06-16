from setuptools import setup
import os

include_dirs = ['docker', 'django', 'scripts', 'notebooks']
base_dir = os.path.join('share', 'esper')
data_files = [(os.path.join(base_dir, path), [os.path.join(path, f)])
              for dir in include_dirs for path, _, filenames in os.walk(dir)
              for f in filenames if 'node_modules' not in path]

if __name__ == "__main__":
    setup(
        name='esper',
        version='0.1.0',
        description='A framework for end-to-end video analytics',
        url='http://github.com/scanner-research/esper',
        author='Will Crichton',
        author_email='wcrichto@cs.stanford.edu',
        license='Apache 2.0',
        entry_points={'console_scripts': ['esper=esper.configure:main']},
        install_requires=['docker-compose', 'pyyaml', 'toml', 'dotmap'],
        #data_files=data_files,
        include_package_data=True,
        packages=['esper'],
        zip_safe=False)
