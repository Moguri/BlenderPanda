Managing Projects
=================

pman
----
``pman`` is a Python module used by BlenderPanda to help manage Panda3D projects.
It has no dependencies on Blender's ``bpy`` nor any Panda3D modules, which means it can be used in custom scripts as well.

Configuration
^^^^^^^^^^^^^
``pman`` has two config files that can be used to configure projects: ``.pman`` and ``.pman.user``.
The ``.pman`` file controls project settings that should affect all users running this project, and it should be submitted to version control.
``.pman.user`` are per-user settings for a project, and it should not be submitted to version control.
These per-user settings can be configuration options such as paths to various programs on a users machine.
These INI-style files contain key-value pairs divided into sections.
Here is an example ``.pman`` file::

    [general]
    name = Game
    render_plugin = game/bamboo/rendermanager.py

    [build]
    asset_dir = assets/
    export_dir = game/assets/
    ignore_exts = blend1, blend2

    [run]
    main_file = game/main.py
    auto_build = True

``.pman`` Options
"""""""""""""""""

**general options**

*name*
   The name of the project.
   This is not currently used for anything.

*render_plugin*
    A path to a python file containing a :ref:`render manager <render_managers>`.

**build options**

*asset_dir*
    The directory to look for source files (e.g., blend files) that need to be converted.

*export_dir*
    The directory to place all converted assets in.
    This folder is created during the build step and should not be put under version control.

*ignore_patterns*
    A comma separated list of Python `fnmatch <https://docs.python.org/3/library/fnmatch.html>`_ patterns.
    Any files in the ``asset_dir`` matching one or more of these patterns will not be converted.

**run options**

*main_file*
    A path to the Python file that contains the entry point for running the game with Panda3D.
    This is usually the file setting up and running `ShowBase <https://www.panda3d.org/manual/index.php/Starting_Panda3D>`_.

*auto_build*
    When set to True, the project is built (files are converted) every time the project is run.
    Only outdated files are converted, which makes building very quick if everything is already converted.

*auto_save*
    When set to True, the current open file in Blender is saved when using the RunProject operator.

``.pman.user`` Options
""""""""""""""""""""""

**blender options**

*last_path*
    The full path to the last Blender binary that opened the project.
    This can be used to avoid putting a Blender binary in an environment PATH variable.
    If Blender is not in the PATH, make sure to open the project in Blender once before trying to run/build the project from the command line.

*use_last_path*
    If this option is set to True, ``pman`` will use the ``last_path`` config value when it needs to launch Blender (e.g., when doing conversion).
    If this value is set to False, then ``blender`` must be on the system PATH.

.. _render_managers:

Render Managers
---------------
TODO
