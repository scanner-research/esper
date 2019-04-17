# Esper: a framework for end-to-end video analytics

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
$ git clone --recursive https://github.com/scanner-research/esper
$ cd esper
$ pip3 install -r requirements.txt
$ python3 configure.py --config config/local.toml
$ docker-compose up -d
$ docker-compose exec app ./deps/install-rust.sh
$ docker-compose exec app bash -c "source /root/.cargo/env && ./deps/install.sh"
$ docker-compose exec app bash -c "npm install && npm run build"
```

**:warning: WARNING :warning:**: Esper is a tool for programmers. It uses a programmatic query interface, which means we use **_REMOTE CODE EXECUTION_** to run queries. DO NOT expose this interface publicly, or else risk having a hacker trash your computer, data, and livelihood.
