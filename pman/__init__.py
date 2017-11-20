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
    return PMan(config=config).get_abs_path(path)


def get_rel_path(config, path):
    return PMan(config=config).get_rel_path(path)


def get_python_program(config=None):
    return PMan(config=config).get_python_program()


def build(config=None):
    PMan(config=config).build()


def run(config=None):
    PMan(config=config).run()


class Converter:
    def __init__(self, supported_exts, ext_dst_map=None):
        self.supported_exts = supported_exts
        self.ext_dst_map = ext_dst_map if ext_dst_map is not None else {}

    def __call__(self, func):
        func.supported_exts = self.supported_exts
        func.ext_dst_map = self.ext_dst_map
        return func


@Converter(['.blend'], {'.blend': '.bam'})
def converter_blend_bam(_config, user_config, srcdir, dstdir, _assets):
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


def converter_copy(_config, _user_config, srcdir, dstdir, assets):
    for asset in assets:
        src = asset
        dst = src.replace(srcdir, dstdir)
        print('Copying non-blend file from "{}" to "{}"'.format(src, dst))
        if not os.path.exists(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        shutil.copyfile(src, dst)


class PMan:
    def __init__(self, config=None, config_startdir=None):
        if config:
            self.config = config
            self.user_config = get_user_config(config.get('internal', 'projectdir'))
        else:
            self.config = get_config(config_startdir)
            self.user_config = get_user_config(config_startdir)

        # TODO: Get these from config
        self.converters = [
            converter_blend_bam,
        ]


    def get_abs_path(self, path):
        return os.path.join(
            self.config.get('internal', 'projectdir'),
            path
        )

    def get_rel_path(self, path):
        return os.path.relpath(path, self.config.get('internal', 'projectdir'))

    def get_python_program(self):
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

    def build(self):
        if is_frozen():
            raise FrozenEnvironmentError()

        if hasattr(time, 'perf_counter'):
            stime = time.perf_counter()
        else:
            stime = time.time()
        print("Starting build")

        srcdir = self.get_abs_path(self.config.get('build', 'asset_dir'))
        dstdir = self.get_abs_path(self.config.get('build', 'export_dir'))

        if not os.path.exists(srcdir):
            raise BuildError("Could not find asset directory: {}".format(srcdir))

        if not os.path.exists(dstdir):
            print("Creating asset export directory at {}".format(dstdir))
            os.makedirs(dstdir)

        print("Read assets from: {}".format(srcdir))
        print("Export them to: {}".format(dstdir))

        ignore_patterns = [i.strip() for i in self.config.get('build', 'ignore_patterns').split(',')]
        print("Ignoring file patterns: {}".format(ignore_patterns))

        # Gather files and group by extension
        ext_asset_map = {}
        ext_dst_map = {}
        ext_converter_map = {}
        for converter in self.converters:
            ext_dst_map.update(converter.ext_dst_map)
            for ext in converter.supported_exts:
                ext_converter_map[ext] = converter

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

                ext = os.path.splitext(asset)[1]

                if ext in ext_dst_map:
                    dst = dst.replace(ext, ext_dst_map[ext])

                if os.path.exists(dst) and os.stat(src).st_mtime <= os.stat(dst).st_mtime:
                    print('Skip building up-to-date file: {}'.format(dst))
                    continue

                if ext not in ext_asset_map:
                    ext_asset_map[ext] = []

                print('Adding {} to conversion list to satisfy {}'.format(src, dst))
                ext_asset_map[ext].append(os.path.join(root, asset))

        # Run conversion hooks
        for ext, converter in ext_converter_map.items():
            if ext in ext_asset_map:
                converter(self.config, self.user_config, srcdir, dstdir, ext_asset_map[ext])
                del ext_asset_map[ext]

        # Copy what is left
        for ext in ext_asset_map:
            converter_copy(self.config, self.user_config, srcdir, dstdir, ext_asset_map[ext])

        if hasattr(time, 'perf_counter'):
            etime = time.perf_counter()
        else:
            etime = time.time()
        print("Build took {:.4f}s".format(etime - stime))

    def run(self):
        if is_frozen():
            raise FrozenEnvironmentError()

        mainfile = self.get_abs_path(self.config.get('run', 'main_file'))
        print("Running main file: {}".format(mainfile))
        args = [self.get_python_program(), mainfile]
        #print("Args: {}".format(args))
        subprocess.Popen(args, cwd=self.config.get('internal', 'projectdir'))
