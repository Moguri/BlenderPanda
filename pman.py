import os
import shutil
import subprocess
import sys
import time
from collections import OrderedDict
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


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
        ('ignore_exts', 'blend1, blend2'),
    ])),
    ('run', OrderedDict([
        ('main_file', 'game/main.py'),
        ('auto_build', True),
    ])),
])


def __py2_read_dict(config, d):
    for section, options in d.items():
        config.add_section(section)

        for option, value in options.items():
            config.set(section, option, value)


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
            if hasattr(config, 'read_dict'):
                config.read_dict(_config_defaults)
            else:
                __py2_read_dict(config, _config_defaults)
            config.read(configpath)

            config.add_section('internal')
            config.set('internal', 'projectdir', os.path.dirname(configpath))
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
        'import panda3d.core; import direct',
    ]
    with open(os.devnull, 'w') as fp:
        retcode = subprocess.call(args, stderr=fp)

    if retcode == 0:
        return 'python3'

    # python3 didn't work, try python2
    args[0] = 'python2'
    with open(os.devnull, 'w') as fp:
        retcode = subprocess.call(args, stderr=fp)

    if retcode == 0:
        return 'python2'

    # We couldn't find a python program to run
    raise CouldNotFindPythonError('Could not find a usable Python install')


def write_config(config):
    writecfg = configparser.ConfigParser()
    writecfg.read_dict(config)
    writecfg.remove_section('internal')

    with open(os.path.join(config.get('internal', 'projectdir'), '.pman'), 'w') as f:
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
    ]

    bpanda_mod_files = [
        os.path.join(templatedir, '__init__.py'),
        os.path.join(templatedir, 'bpbase.py'),
        'rendermanager.py',
        'pman.py',
        'pman_build.py',
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

   
    bpmodpath = os.path.join(projectdir, 'game/blenderpanda')
    if os.path.exists(bpmodpath):
        print("Updating blenderpanda module")
        shutil.rmtree(bpmodpath)
    else:
        print("Creating blenderpanda module")
    os.mkdir(bpmodpath)
    for cf in bpanda_mod_files:
        bname = os.path.basename(cf)
        print("\tCopying over {}".format(bname))
        cfsrc = os.path.join(os.path.dirname(__file__), cf)
        cfdst = os.path.join(projectdir, 'game', 'blenderpanda', bname)
        shutil.copy(cfsrc, cfdst)
        print("\t\t{} created at {}".format(bname, cfdst))


def get_abs_path(config, path):
    return os.path.join(
        config.get('internal', 'projectdir'),
        path
    )


def get_rel_path(config, path):
    return os.path.relpath(path, config.get('internal', 'projectdir'))


def build(config=None):
    if config is None:
        config = get_config()

    if hasattr(time, 'perf_counter'):
        stime = time.perf_counter()
    else:
        stime = time.time()
    print("Starting build")

    srcdir = get_abs_path(config, config.get('build', 'asset_dir'))
    dstdir = get_abs_path(config, config.get('build', 'export_dir'))

    if not os.path.exists(srcdir):
        raise BuildError("Could not find asset directory: {}".format(srcdir))

    if not os.path.exists(dstdir):
        print("Creating asset export directory at {}".format(dstdir))
        os.makedirs(dstdir)

    print("Read assets from: {}".format(srcdir))
    print("Export them to: {}".format(dstdir))

    ignore_exts = [i.strip() for i in config.get('build', 'ignore_exts').split(',')]
    print("Ignoring extensions: {}".format(ignore_exts))

    num_blends = 0
    for root, dirs, files in os.walk(srcdir):
        for asset in files:
            src = os.path.join(root, asset)
            dst = src.replace(srcdir, dstdir)

            iext = None
            for ext in ignore_exts:
                if asset.endswith(ext):
                    iext = ext
                    break
            if iext is not None:
                print('Skip building file with ignored extension ({}): {}'.format(iext, dst))
                continue

            if asset.endswith('.blend'):
                dst = dst.replace('.blend', '.bam')

            if os.path.exists(dst) and os.stat(src).st_mtime <= os.stat(dst).st_mtime:
                print('Skip building up-to-date file: {}'.format(dst))
                continue

            if asset.endswith('.blend'):
                # Handle with Blender
                num_blends += 1
            else:
                print('Copying non-blend file from "{}" to "{}"'.format(src, dst))
                if not os.path.exists(os.path.dirname(dst)):
                    os.makedirs(os.path.dirname(dst))
                shutil.copyfile(src, dst)

    if num_blends > 0:
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

    if hasattr(time, 'perf_counter'):
        etime = time.perf_counter()
    else:
        etime = time.time()
    print("Build took {:.4f}s".format(etime - stime))


def run(config=None):
    if config is None:
        config = get_config()

    if config.getboolean('run', 'auto_build'):
        build(config)

    mainfile = get_abs_path(config, config.get('run', 'main_file'))
    print("Running main file: {}".format(mainfile))
    args = [get_python_program(config), mainfile]
    #print("Args: {}".format(args))
    subprocess.Popen(args, cwd=config.get('internal', 'projectdir'))
