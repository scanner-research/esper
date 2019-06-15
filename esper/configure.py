import argparse
import yaml
import toml
import subprocess as sp
import shlex
from dotmap import DotMap
import multiprocessing
import shutil
import socket
import os
import pathlib

REPO_DIR = os.path.join(os.path.dirname(__file__), '..')
DJANGO_DIR = os.path.join(REPO_DIR, 'django')
DOCKER_DIR = os.path.join(REPO_DIR, 'docker')
SCRIPTS_DIR = os.path.join(REPO_DIR, 'scripts')

NGINX_PORT = '80'
IPYTHON_PORT = '8888'
TF_VERSION = '1.11.0'

cores = multiprocessing.cpu_count()

def yaml_load(s):
    return DotMap(yaml.safe_load(s))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        '-c',
        required=True,
        help='Path to Esper configuration TOML, e.g. config/default.toml')
    parser.add_argument(
        '--extra-processes',
        nargs='*',
        default=[],
        choices=['npm'],
        help='Optional processes to run by default in application container')
    parser.add_argument('--no-build', action='store_true', help='Don\'t build any Docker images')
    parser.add_argument('--build-tf', action='store_true', help='Build TensorFlow from scratch')
    parser.add_argument(
        '--build-device',
        help='Override to build Docker image for particular device')
    parser.add_argument(
        '--base-only', action='store_true', help='Only build base image, not application image')
    parser.add_argument(
        '--no-pull',
        action='store_true',
        help='Don\'t automatically pull latest scannertools image')
    parser.add_argument(
        '--push-remote',
        action='store_true',
        help='Push base image to Google Cloud Container Registry')
    parser.add_argument(
        '--scannertools-dir', help='Path to Scannertools directory (for development)')
    parser.add_argument(
        '--dotfiles-dir',
        default=os.path.expanduser('~/.esper'),
        help='Path to directory for persistent dotfiles in Docker container')
    parser.add_argument('--hostname', help='Internal use only')
    args = parser.parse_args()

    if not os.path.isdir('docker'):
        shutil.copytree(DOCKER_DIR, 'docker')

    if not os.path.isfile('.dockerignore'):
        shutil.copy(os.path.join(REPO_DIR, '.dockerignore'), '.dockerignore')

    if not os.path.isdir('scripts'):
        shutil.copytree(SCRIPTS_DIR, 'scripts')

    # TODO(wcrichto): validate config file
    base_config = DotMap(toml.load(args.config))

    extra_services = {
        'spark':
        yaml_load("""
    build:
      context: ./docker/spark
      args: {}
    ports: ['7077']
    environment: []
    depends_on: [db]
    volumes:
      - ./app:/app
    """),
        'gentle':
        yaml_load("""
    image: lowerquality/gentle
    environment: []
    ports: ['8765']
    command: bash -c "cd /gentle && python serve.py --ntranscriptionthreads 8"
    """),
        'redis':
        yaml_load("""
    redis:
        image: redis:4
        ports: ['{port}:6379']
        environment: []
    """.format(port=base_config.ports.redis))
    }

    supervisord_conf = """
[supervisord]
nodaemon=true
logfile=/tmp/supervisord.log
pidfile=/tmp/supervisord.pid
user=root
    """

    base_processes = {
        'gunicorn': 'gunicorn --log-file=- -c /django/gunicorn_conf.py django_settings.wsgi:application --reload',
        'notebook': 'python3 /django/manage.py shell_plus --notebook'
    }

    extra_processes = {'npm': 'npm run watch --color'}

    tsize = shutil.get_terminal_size()
    config = yaml_load("""
    version: '2.3'
    services:
      nginx:
        build:
          context: ./docker/nginx
        command: ["bash", "/tmp/subst.sh"]
        volumes:
          - .:/app
          - ./docker/nginx:/tmp
          - {django_dir}:/django
        depends_on: [app, frameserver]
        ports: ["{nginx_port}:80", "{ipython_port}:8888"]
        environment: []

      frameserver:
        image: scannerresearch/frameserver
        ports: ['{frameserver_port}:7500']
        environment: ['WORKERS={workers}']

      app:
        build:
          context: .
          dockerfile: docker/Dockerfile.app
          args:
            cores: {cores}
        depends_on: [db, frameserver]
        volumes:
          - .:/app
          - {django_dir}:/django
          - {repo_dir}:/opt/esper
        ports: ["8000", "{ipython_port}"]
        environment:
          - IPYTHON_PORT={ipython_port}
          - JUPYTER_PASSWORD=esperjupyter
          - COLUMNS={columns}
          - LINES={lines}
          - TERM={term}
          - RUST_BACKTRACE=full
        tty: true # https://github.com/docker/compose/issues/2231#issuecomment-165137408
        privileged: true # make perf work
        security_opt: # make gdb work
          - seccomp=unconfined
    """.format(
            home=os.path.expanduser(base_config.docker.dotfiles_dir),
            nginx_port=base_config.ports.nginx,
            ipython_port=base_config.ports.ipython,
            frameserver_port=base_config.ports.frameserver,
            cores=cores,
            workers=cores * 2,
            columns=tsize.columns,
            lines=tsize.lines,
            term=os.environ.get('TERM'),
            django_dir=DJANGO_DIR,
            repo_dir=REPO_DIR))

    db_options = {
        'local':
        yaml_load("""
    build:
        context: ./docker/db
    environment:
      - POSTGRES_DB=esper
    volumes: ["./data/postgresql:/var/lib/postgresql/data", ".:/app"]
    ports: ["5432"]
    """),

        'google': yaml_load("""
    image: gcr.io/cloudsql-docker/gce-proxy:1.09
    volumes: ["./service-key.json:/config"]
    environment: []
    ports: ["5432"]
    """)
    }


    # Google Cloud config
    if 'google' in base_config:
        if not os.path.isfile('service-key.json'):
            raise Exception("Missing required service key file service-key.json")

        config.services.app.environment.extend([
            'GOOGLE_PROJECT={}'.format(base_config.google.project),
            'GOOGLE_ZONE={}'.format(base_config.google.zone)
        ])

        config.services.app.volumes.append(
          './service-key.json:/app/service-key.json')

    # GPU settings
    device = base_config.docker.device

    build_device = device if args.build_device is None else args.build_device
    config.services.app.build.args.base_name = base_config.docker.base_image_name
    config.services.app.build.args.tag = build_device

    config.services.app.build.args.device = device
    if device != 'cpu':
        config.services.app.runtime = 'nvidia'

    config.services.app.environment.append('DEVICE={}'.format(device))
    config.services.app.image = 'scannerresearch/esper:{}'.format(device)

    if args.scannertools_dir is not None:
        config.services.app.volumes.append('{}:/opt/scannertools'.format(
            os.path.abspath(args.scannertools_dir)))

    # Dotfiles directory
    dotfiles = ['.bash_history']
    dotdirs = ['.cargo', '.rustup', '.local', '.jupyter']

    # Instantiate dotfiles directory
    os.makedirs(args.dotfiles_dir, exist_ok=True)

    # Create any dotfiles like .bash_history as files since otherwise missing mounts
    # will be turned into directories and then not be properly created by the shell
    for f in dotfiles:
        pathlib.Path('{}/{}'.format(args.dotfiles_dir, f)).touch()

    # Add all dotfiles paths as Docker volumes
    for path in dotfiles + dotdirs:
        config.services.app.volumes.append('{dotfiles_dir}/{path}:/root/{path}'.format(
            dotfiles_dir=args.dotfiles_dir, path=path))

    # Additional Docker services
    for svc in base_config.docker.extra_services:
        config.services[svc] = extra_services[svc]
        config.services.app.depends_on.append(svc)

        if svc == 'spark':
            config.services.spark.build.args.base_name = base_config.docker.base_image_name

    # Supervisord proceseses
    all_processes = {**base_processes, **{p: extra_processes[p] for p in args.extra_processes}}

    for process, command in all_processes.items():
        supervisord_conf += """
\n[program:{}]
command={}
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0""".format(process, command)
    with open('supervisord.conf', 'w') as f:
        f.write(supervisord_conf)

    env = ['ESPER_ENV={}'.format(base_config.storage.type),
            'DATA_PATH={}'.format(base_config.storage.path),
            'BASE_IMAGE_NAME={}'.format(base_config.docker.base_image_name)]

    ### SQL database
    config.services.db = db_options[base_config.database.type]

    db_user = base_config.database.user if 'user' in base_config.database else 'root'
    env.extend(['DB_USER={}'.format(db_user), 'POSTGRES_USER={}'.format(db_user)])

    db_password = None
    if 'password' in base_config.database:
        db_password = base_config.database.password
        env.extend([
            'DB_PASSWORD={}'.format(db_password),
            'POSTGRES_PASSWORD={}'.format(db_password),
            'PGPASSWORD={}'.format(db_password)
        ])

    if base_config.database.type == 'google':
        assert 'google' in base_config
        config.services.db['command'] = \
            '/cloud_sql_proxy -instances={project}:{zone}:{name}=tcp:0.0.0.0:5432 -credential_file=/config'.format(
                project=base_config.google.project, zone=base_config.google.zone, name=base_config.database.name)

    ### Scanner config
    scanner_config = {}
    if base_config.storage.type == 'google':
        assert 'google' in base_config
        scanner_config['storage'] = {
            'type': 'gcs',
            'bucket': base_config.storage.bucket,
            'db_path': '{}/scanner_db'.format(base_config.storage.path)
        }
    else:
        scanner_config['storage'] = {'type': 'posix', 'db_path': '/app/data/scanner_db'}

    ### Frameserver
    env.append('FILESYSTEM={}'.format(base_config.storage.type))

    if base_config.storage.type == 'google':
        if not 'AWS_ACCESS_KEY_ID' in os.environ:
            raise Exception('Missing environment variable AWS_ACCESS_KEY_ID')

        if not 'AWS_SECRET_ACCESS_KEY' in os.environ:
            raise Exception('Missing environment variable AWS_SECRET_ACCESS_KEY')

        env.extend([
            'BUCKET={}'.format(base_config.storage.bucket),
            'AWS_ACCESS_KEY_ID={}'.format(os.environ['AWS_ACCESS_KEY_ID']),
            'AWS_SECRET_ACCESS_KEY={}'.format(os.environ['AWS_SECRET_ACCESS_KEY'])
        ])

    ## Get local machine's host name
    if args.hostname is not None:
        hostname = args.hostname
    else:
        try:
            is_google = b'Metadata-Flavor: Google' in sp.check_output(
                'curl metadata.google.internal -i -s', shell=True)
        except sp.CalledProcessError:
            is_google = False

        if is_google:
            hostname = sp.check_output(
                """
            gcloud compute instances list --format=json | \
            jq ".[] | select(.name == \\"$(hostname)\\") | \
                .networkInterfaces[0].accessConfigs[] | \
                select(.name == \\"External NAT\\") | .natIP" -r
            """,
                shell=True).decode('utf-8').strip()
        else:
            hostname = socket.gethostbyname(socket.gethostname())
    env.append('HOSTNAME={}'.format(hostname))

    ## Add env vars to each service
    for service in list(config.services.values()):
        service.environment.extend(env)

    ### Write out generated configuration files
    with open('.scanner.toml', 'w') as f:
        f.write(toml.dumps(scanner_config))

    with open('docker-compose.yml', 'w') as f:
        f.write(yaml.dump(config.toDict()))

    ### Build Docker images where necessary
    if not args.no_build:

        if args.build_tf:
            print("""wcrichto 12-7-18: observed that custom built TF version 1.11.0
            was causing a ~10x slowdown versus pip installed. Shouldn't use custom build
            until that's debugged.""")
            exit(1)

        base_name = base_config.docker.base_image_name

        build_args = {
            'cores': cores,
            'base_name': base_config.docker.base_image_name,
            'tag': build_device,
            'device': build_device,
            'tf_version': TF_VERSION,
            'build_tf': 'on' if args.build_tf else 'off'
        }

        sp.check_call(
            'docker build {pull} -t {base_name}:{device} {build_args} -f docker/Dockerfile.base .' \
            .format(
                device=build_device,
                base_name=base_name,
                pull='--pull' if not args.no_pull else '',
                build_args=' '.join(
                    ['--build-arg {}={}'.format(k, v) for k, v in build_args.items()])),
            shell=True)

        if 'google' in base_config and args.push_remote:
            base_url = 'gcr.io/{project}'.format(project=base_config.google.project)
            sp.check_call(
                'docker tag {base_name}:{device} {base_url}/{base_name}:{device} && \
                gcloud docker -- push {base_url}/{base_name}:{device}'.format(
                    device=build_device, base_name=base_name, base_url=base_url),
                shell=True)

        if not args.base_only:
            sp.check_call('docker-compose build app', shell=True)

    print('Successfully configured Esper. To start Esper, run:')
    print('$ docker-compose up -d')


if __name__ == '__main__':
    main()
