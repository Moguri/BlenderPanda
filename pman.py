import configparser
import os
import shutil
import subprocess
import sys
import time
from collections import OrderedDict


class PManException(Exception):
    def __init__(self, value):
        self.value = value


class NoConfigError(PManException):
    pass


class CouldNotFindPythonError(PManException):
    pass


class BuildError(PManException):
    pass


_config_defaults = OrderedDict([
    ('general', OrderedDict([
        ('name', 'Game'),
        ('render_plugin', ''),
    ])),
    ('build', OrderedDict([
        ('asset_dir', 'assets/'),
        ('export_dir', 'game/assets/'),
    ])),
    ('run', OrderedDict([
        ('main_file', 'game/main.py'),
        ('auto_build', True),
    ])),
])


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


def get_python_program(config):
    # Always use ppython on Windows
    if sys.platform == 'win32':
        return 'ppython'

    # Check to see if there is a version of Python that can import panda3d
    args = [
        'python3',
        '-c',
        '"import panda3d.core"',
    ]
    retcode = subprocess.call(args)

    if retcode == 0:
        return 'python3'

    # python3 didn't work, try python2
    args[0] = 'python2'
    retcode = subprocess.call(args)

    if retcode == 0:
        return 'python2'

    # We couldn't find a python program to run
    raise CouldNotFindPythonError('Could not find a usable Python install')


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

    stime = time.perf_counter()
    print("Starting build")

    srcdir = get_abs_path(config, config['build']['asset_dir'])
    dstdir = get_abs_path(config, config['build']['export_dir'])

    if not os.path.exists(srcdir):
        raise BuildError("Could not find asset directory: {}".format(srcdir))

    if not os.path.exists(dstdir):
        print("Creating asset export directory at {}".format(dstdir))
        os.makedirs(dstdir)

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
