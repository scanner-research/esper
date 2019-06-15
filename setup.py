from setuptools import setup

if __name__ == "__main__":
    setup(name='esper',
          version='0.1.0',
          description='A framework for end-to-end video analytics',
          url='http://github.com/scanner-research/esper',
          author='Will Crichton',
          author_email='wcrichto@cs.stanford.edu',
          license='Apache 2.0',
          entry_points={'console_scripts': ['esper=esper.configure:main']},
          install_requires=[
              'docker-compose==1.24.0',
              'pyyaml==5.1',
              'toml==0.10.0',
              'dotmap==1.3.8'
          ]
          packages=['esper'],
          zip_safe=False)
