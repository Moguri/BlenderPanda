import os
import configparser
import subprocess
import shutil
import time


class PManException(Exception):
    def __init__(self, value):
        self.value = value


class NoConfigError(PManException):
    pass


_config_defaults = {
    'general': {
        'name': 'Game',
        'render_plugin': '',
    },
    'build': {
        'asset_dir': 'assets/',
        'export_dir': 'game/assets/',
    },
    'run': {
        'main_file': 'game/main.py',
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
        cdir = os.sep.join(dirs)
        if cdir.strip() and '.pman' in os.listdir(cdir):
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


def write_config(config):
    writecfg = configparser.ConfigParser()
    writecfg.read_dict(config)
    writecfg.remove_section('internal')

    with open(os.path.join(config['internal']['projectdir'], '.pman'), 'w') as f:
        writecfg.write(f)


def create_project(projectdir):
    confpath = os.path.join(projectdir, '.pman')
    if os.path.exists(confpath):
        print("Updating project in {}".format(projectdir))
    else:
        print("Creating new project in {}".format(projectdir))

        # Touch config file to make sure it is present
        with open(confpath, 'a') as f:
            pass

    config = get_config(projectdir)
    write_config(config)

    templatedir = os.path.join(os.path.dirname(__file__), 'templates')

    print("Creating directories...")

    dirs = [
        'assets',
        'game',
        'game/assets',
        'game/blenderpanda',
    ]

    copy_files = [
        os.path.join(templatedir, '__init__.py'),
        os.path.join(templatedir, 'bpbase.py'),
        'rendermanager.py',
        'pman.py',
    ]

    dirs = [os.path.join(projectdir, i) for i in dirs]

    for d in dirs:
        if os.path.exists(d):
            print("\tSkipping existing directory: {}".format(d))
        else:
            print("\tCreating directory: {}".format(d))
            os.mkdir(d)

    print("Creating main.py")
    with open(os.path.join(templatedir, 'main.py')) as f:
        main_data = f.read()

    mainpath = os.path.join(projectdir, 'game', 'main.py')
    if os.path.exists(mainpath):
        print("\tmain.py already exists at {}".format(mainpath))
    else:
        with open(mainpath, 'w') as f:
            f.write(main_data)
        print("\tmain.py created at {}".format(mainpath))

    print("Creating blenderpanda module")
    for cf in copy_files:
        bname = os.path.basename(cf)
        print("\tCopying over {}".format(bname))
        cfsrc = os.path.join(os.path.dirname(__file__), cf)
        cfdst = os.path.join(projectdir, 'game', 'blenderpanda', bname)
        if os.path.exists(cfdst):
            print("\t\t{} already exists at {}".format(bname, cfdst))
        else:
            shutil.copy(cfsrc, cfdst)
            print("\t\t{} created at {}".format(bname, cfdst))


def get_abs_path(config, path):
    return os.path.join(
        config['internal']['projectdir'],
        path
    )


def get_rel_path(config, path):
    return os.path.relpath(path, config['internal']['projectdir'])


def build(config=None):
    if config is None:
        config = get_config()

    srcdir = get_abs_path(config, config['build']['asset_dir'])
    dstdir = get_abs_path(config, config['build']['export_dir'])

    stime = time.perf_counter()

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

    subprocess.call(args, env=os.environ.copy())

    print("Build took {:.4f}s".format(time.perf_counter() - stime))


def run(config=None):
    if config is None:
        config = get_config()

    if config.getboolean('run', 'auto_build'):
        build(config)

    mainfile = get_abs_path(config, config['run']['main_file'])
    print("Running main file: {}".format(mainfile))
    args = ['python', mainfile]
    #print("Args: {}".format(args))
    subprocess.Popen(args)
