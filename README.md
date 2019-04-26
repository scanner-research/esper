# Esper: a framework for end-to-end video analytics

Esper is a development environment that provides out-of-the-box integration for a variety of tools useful for analyzing videos, including:
* [Scanner](https://github.com/scanner-research/scanner): high-performance parallel processing of videos
* [Rekall](https://github.com/scanner-research/rekall): data representation and operations for spatiotemporal data in Python
* [VGrid](https://github.com/scanner-research/vgrid): visualizing metadata on videos using Python and Javascript
* [Frameserver](https://github.com/scanner-research/frameserver): dynamically extracting frames from a video
* [Django](https://docs.djangoproject.com/en/2.2/): managing SQL models and serving web pages
* [Spark](https://spark.apache.org/): parallel analysis of metadata

Esper is kind of like Ruby on Rails but for video analytics. It provides a skeleton of a data science workbench that you can customize for your particular project, along with a set of useful utility functions, models, preinstalled dependencies, and so on.

**:warning: WARNING :warning:**: Esper is a tool for programmers. It uses a programmatic query interface, which means we use **_REMOTE CODE EXECUTION_** to run queries. DO NOT expose this interface publicly, or else risk having a hacker trash your computer, data, and livelihood.

## Setup

First, install [Docker CE](https://docs.docker.com/engine/installation/#supported-platforms), [Python 3.5](https://www.python.org/downloads/), [jq](https://stedolan.github.io/jq/download/), and [pip](https://pip.pypa.io/en/stable/installing/). If you're on Ubuntu, you can install Python/pip/jq as follows:
```
sudo apt-get install python3 python3-pip jq
```

Ensure that you have Docker version >= 17.12, which you can check by running:
```
$ docker --version
Docker version 17.12.0-ce, build c97c6d6
```

> Note: If you have a GPU and are running on Linux, then install [nvidia-docker2.](https://github.com/NVIDIA/nvidia-docker). Set `device = "gpu-9.1-cudnn7` in `config/local.toml`.

Next, you will need to configure your Esper installation.

```
$ git clone https://github.com/scanner-research/esper
$ cd esper
$ pip3 install -r requirements.txt
$ python3 configure.py --config config/local.toml
$ docker-compose up -d
$ docker-compose run app bash -c "cd ui && npm install && npm run prepublishOnly"
```

### Esper developers

If you're developing the Esper core platform or otherwise want to stay up to date with our dependencies, then you should clone and link our submodules.

```
$ git submodule update --init --recursive
$ docker-compose run app bash -c "./deps/install.sh"
```
