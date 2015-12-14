import os
import configparser
import subprocess


class PManException(Exception):
    def __init__(self, value):
        self.value = value


class NoConfigError(PManException):
    pass


def get_config(startdir=None):
    if startdir is None:
        startdir = os.getcwd()

    dirs = os.path.abspath(startdir).split(os.sep)

    while dirs:
        cdir = os.path.join(os.sep, *dirs)
        if '.pman' in os.listdir(cdir):
            config = configparser.ConfigParser()
            config.read(os.path.join(cdir, '.pman'))
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
    config['general'] = {}
    config['general']['name'] = appname

    config['build'] = {}
    config['build']['asset_dir'] = os.path.join(projectdir, 'assets')
    config['build']['export_dir'] = os.path.join(projectdir, 'src/assets')

    config['run'] = {}
    config['run']['main_file'] = os.path.join(projectdir, 'src/main.py')

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
        main_data = f.read().replace('APP_NAME', appname)

    mainpath = os.path.join(projectdir, 'src', 'main.py')
    if os.path.exists(mainpath):
        print("\tmain.py already exists at {}".format(mainpath))
    else:
        with open(mainpath, 'w') as f:
            f.write(main_data)
        print("\tmain.py created at {}".format(mainpath))


def build():
    config = get_config()

    print("Read assets from: {}".format(config['build']['asset_dir']))
    print("Export them to: {}".format(config['build']['export_dir']))


def run():
    config = get_config()

    print("Running main file: {}".format(config['run']['main_file']))
    args = ['python', config['run']['main_file']]
    #print("Args: {}".format(args))
    subprocess.Popen(args)
