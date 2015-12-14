import os
import configparser
import subprocess


class PManException(Exception):
    def __init__(self, value):
        self.value = value


class NoConfigError(PManException):
    pass


_config_defaults = {
    'general': {
        'name': 'Game',
    },
    'build': {
        'asset_dir': 'assets',
        'export_dir': 'src/assets',
    },
    'run': {
        'main_file': 'src/main.py',
        'auto_build': True,
    }
}


def get_config(startdir=None):
    try:
        if startdir is None:
            startdir = os.getcwd()
    except FileNotFoundError:
        # The project folder was deleted on us
        raise NoConfigError("Could not find config file")

    dirs = os.path.abspath(startdir).split(os.sep)

    while dirs:
        cdir = os.path.join(os.sep, *dirs)
        if '.pman' in os.listdir(cdir):
            configpath = os.path.join(cdir, '.pman')
            config = configparser.ConfigParser()
            config.read_dict(_config_defaults)
            config.read(configpath)

            config['internal'] = {}
            config['internal']['projectdir'] = os.path.dirname(configpath)
            return config

        dirs.pop()

    # No config found
    raise NoConfigError("Could not find config file")


def create_project(projectdir, appname):
    print("Creating new project in", projectdir)

    appname = appname.replace(' ', '')

    with open(os.path.join(projectdir, '.pman'), 'w') as f:
        pass

    config = get_config(projectdir)
    config['general']['name'] = appname

    with open(os.path.join(projectdir, '.pman'), 'w') as f:
        config.write(f)

    print("Creating directories...")

    dirs = [
        'assets',
        'src',
        'src/assets',
        'src/config',
        'src/{}'.format(appname),
    ]

    dirs = [os.path.join(projectdir, i) for i in dirs]

    for d in dirs:
        if os.path.exists(d):
            print("\tSkipping existing directory: {}".format(d))
        else:
            print("\tCreating directory: {}".format(d))
            os.mkdir(d)

    print("Creating main.py")
    templatedir = os.path.join(os.path.dirname(__file__), 'templates')
    with open(os.path.join(templatedir, 'main.py')) as f:
        main_data = f.read()

    mainpath = os.path.join(projectdir, 'src', 'main.py')
    if os.path.exists(mainpath):
        print("\tmain.py already exists at {}".format(mainpath))
    else:
        with open(mainpath, 'w') as f:
            f.write(main_data)
        print("\tmain.py created at {}".format(mainpath))


def get_abs_path(config, path):
    return os.path.join(
        config['internal']['projectdir'],
        path
    )


def build():
    config = get_config()

    srcdir = get_abs_path(config, config['build']['asset_dir'])
    dstdir = get_abs_path(config, config['build']['export_dir'])

    print("Read assets from: {}".format(srcdir))
    print("Export them to: {}".format(dstdir))

    args = [
        'blender',
        '-b',
        '-P',
        os.path.join(os.path.dirname(__file__), 'pman_build.py'),
        '--',
        srcdir,
        dstdir,
    ]

    subprocess.call(args)


def run():
    config = get_config()

    if config.getboolean('run', 'auto_build'):
        build()

    mainfile = get_abs_path(config, config['run']['main_file'])
    print("Running main file: {}".format(mainfile))
    args = ['python', mainfile]
    #print("Args: {}".format(args))
    subprocess.Popen(args)
