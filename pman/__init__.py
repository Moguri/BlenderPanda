import fnmatch
import os
import shutil
import subprocess
import time
from collections import OrderedDict
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class PManException(Exception):
    pass


class NoConfigError(PManException):
    pass


class CouldNotFindPythonError(PManException):
    pass


class BuildError(PManException):
    pass


class FrozenEnvironmentError(PManException):
    def __init__(self):
        PManException.__init__(self, "Operation not supported in frozen applications")


if '__file__' not in globals():
    __IS_FROZEN = True
    __file__ = ''
else:
    __IS_FROZEN = False


_CONFIG_DEFAULTS = OrderedDict([
    ('general', OrderedDict([
        ('name', 'Game'),
        ('render_plugin', ''),
    ])),
    ('build', OrderedDict([
        ('asset_dir', 'assets/'),
        ('export_dir', 'game/assets/'),
        ('ignore_patterns', '*.blend1, *.blend2'),
    ])),
    ('run', OrderedDict([
        ('main_file', 'game/main.py'),
        ('auto_build', True),
        ('auto_save', True),
    ])),
])

_USER_CONFIG_DEFAULTS = OrderedDict([
    ('blender', OrderedDict([
        ('last_path', 'blender'),
        ('use_last_path', True),
    ])),
])


def __py2_read_dict(config, d):
    for section, options in d.items():
        config.add_section(section)

        for option, value in options.items():
            config.set(section, option, value)

def _get_config(startdir, conf_name, defaults):
    try:
        if startdir is None:
            startdir = os.getcwd()
    except FileNotFoundError:
        # The project folder was deleted on us
        raise NoConfigError("Could not find config file")

    dirs = os.path.abspath(startdir).split(os.sep)

    while dirs:
        cdir = os.sep.join(dirs)
        if cdir.strip() and conf_name in os.listdir(cdir):
            configpath = os.path.join(cdir, conf_name)
            config = configparser.ConfigParser()
            if hasattr(config, 'read_dict'):
                config.read_dict(defaults)
            else:
                __py2_read_dict(config, defaults)
            config.read(configpath)

            config.add_section('internal')
            config.set('internal', 'projectdir', os.path.dirname(configpath))
            return config

        dirs.pop()

    # No config found
    raise NoConfigError("Could not find config file")


def get_config(startdir=None):
    return _get_config(startdir, '.pman', _CONFIG_DEFAULTS)


def config_exists(startdir=None):
    try:
        get_config(startdir)
        have_config = True
    except NoConfigError:
        have_config = False

    return have_config


def get_user_config(startdir=None):
    try:
        return _get_config(startdir, '.pman.user', _USER_CONFIG_DEFAULTS)
    except NoConfigError:
        # No user config, just create one
        config = get_config(startdir)
        file_path = os.path.join(config.get('internal', 'projectdir'), '.pman.user')
        print("Creating user config at {}".format(file_path))
        open(file_path, 'w').close()

        return _get_config(startdir, '.pman.user', _USER_CONFIG_DEFAULTS)


def _write_config(config, conf_name):
    writecfg = configparser.ConfigParser()
    writecfg.read_dict(config)
    writecfg.remove_section('internal')

    with open(os.path.join(config.get('internal', 'projectdir'), conf_name), 'w') as f:
        writecfg.write(f)


def write_config(config):
    _write_config(config, '.pman')


def write_user_config(user_config):
    _write_config(user_config, '.pman.user')


def is_frozen():
    return __IS_FROZEN


def get_python_program(_config):
    python_programs = [
        'ppython',
        'python3',
        'python',
        'python2',
    ]

    # Check to see if there is a version of Python that can import panda3d
    for pyprog in python_programs:
        args = [
            pyprog,
            '-c',
            'import panda3d.core; import direct',
        ]
        with open(os.devnull, 'w') as f:
            try:
                retcode = subprocess.call(args, stderr=f)
            except FileNotFoundError:
                retcode = 1

        if retcode == 0:
            return pyprog

    # We couldn't find a python program to run
    raise CouldNotFindPythonError('Could not find a usable Python install')


def create_project(projectdir):
    if is_frozen():
        raise FrozenEnvironmentError()

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

    pmandir = os.path.dirname(__file__)
    templatedir = 'templates'

    print("Creating directories...")

    dirs = [
        'assets',
        'game',
    ]

    bpanda_mod_files = [
        os.path.join(templatedir, '__init__.py'),
        os.path.join(templatedir, 'bpbase.py'),
        'rendermanager.py',
        'pman',
    ]

    dirs = [os.path.join(projectdir, i) for i in dirs]

    for d in dirs:
        if os.path.exists(d):
            print("\tSkipping existing directory: {}".format(d))
        else:
            print("\tCreating directory: {}".format(d))
            os.mkdir(d)

    print("Creating main.py")
    with open(os.path.join(pmandir, '..', templatedir, 'main.py')) as f:
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
    for copy_file in bpanda_mod_files:
        bname = os.path.basename(copy_file)
        print("\tCopying over {}".format(bname))
        cfsrc = os.path.join(os.path.dirname(__file__), '..', copy_file)
        cfdst = os.path.join(projectdir, 'game', 'blenderpanda', bname)
        print(cfsrc, cfdst)
        if os.path.isdir(cfsrc):
            shutil.copytree(cfsrc, cfdst)
        else:
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
    if is_frozen():
        raise FrozenEnvironmentError()

    if config is None:
        config = get_config()
    user_config = get_user_config(config.get('internal', 'projectdir'))

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

    ignore_patterns = [i.strip() for i in config.get('build', 'ignore_patterns').split(',')]
    print("Ignoring file patterns: {}".format(ignore_patterns))

    num_blends = 0
    for root, _dirs, files in os.walk(srcdir):
        for asset in files:
            src = os.path.join(root, asset)
            dst = src.replace(srcdir, dstdir)

            ignore_pattern = None
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(asset, pattern):
                    ignore_pattern = pattern
                    break
            if ignore_pattern is not None:
                print('Skip building file {} that matched ignore pattern {}'.format(asset, ignore_pattern))
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
        use_last_path = user_config.getboolean('blender', 'use_last_path')
        blender_path = user_config.get('blender', 'last_path') if use_last_path else 'blender'
        args = [
            blender_path,
            '-b',
            '-P',
            os.path.join(os.path.dirname(__file__), 'pman_build.py'),
            '--',
            srcdir,
            dstdir,
        ]

        #print("Calling blender: {}".format(' '.join(args)))

        subprocess.call(args, env=os.environ.copy())

    if hasattr(time, 'perf_counter'):
        etime = time.perf_counter()
    else:
        etime = time.time()
    print("Build took {:.4f}s".format(etime - stime))


def run(config=None):
    if is_frozen():
        raise FrozenEnvironmentError()

    if config is None:
        config = get_config()

    if config.getboolean('run', 'auto_build'):
        build(config)

    mainfile = get_abs_path(config, config.get('run', 'main_file'))
    print("Running main file: {}".format(mainfile))
    args = [get_python_program(config), mainfile]
    #print("Args: {}".format(args))
    subprocess.Popen(args, cwd=config.get('internal', 'projectdir'))
