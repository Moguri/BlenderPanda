Getting Started
===============

Installing BlenderPanda
-----------------------

Dependencies
^^^^^^^^^^^^

In order to use BlenderPanda, you need to satisfy two dependencies:

* Blender (tested with 2.77)
* Python with Panda3D SDK (Python 2 and Python 3 are both supported)

.. note::
    The Windows Panda3D SDK installer ships with its own version of Python.
    This makes a separate Python install uncessary.

The Python binary that has the Panda SDK installed needs to be on the PATH for BlenderPanda to work.
On Windows this will likely be the ``ppython.exe`` that ships with the Panda3D SDK.

Installing the Addon
^^^^^^^^^^^^^^^^^^^^

After dependencies downloaded and setup, it is time to install the addon itself.
GitHub's Download ZIP option does not support git submodules, which are used by BlenderPanda to bring in the `BlenderRealtimeEngineAddon <https://github.com/Kupoman/BlenderRealtimeEngineAddon>`_.
This makes `git <https://git-scm.com/>`_ the recommended way to grab the addon.
In the future, packaged releases will be made that will not require git.
From the user addons directory (e.g., ~/.config/blender/2.xx/scripts/addons on Linux) use the following git command::

    git clone --recursive https://github.com/Moguri/BlenderPanda.git

To update to the latest version of the addon run the following from the addon's directory::

    git pull
    git submodule update --init --recursive

With the addon repository cloned, the addon should now show up in the addons section of Blender's User Preferences and can be enabled from there.
If all has gone well, a Panda3D RenderEngine should now be available.
If the addon has been enabled, but does not show up in the RenderEngine drop down, check the console for errors.

The mostly likely source of errors is not having Panda3D setup correctly.
If, instead, there is an error about not being able to find brte or a submodule in brte, the git repository is likely missing its submodules.
This can happen if the ``--recursive`` option was not used.
The following git command should bring in the missing submodule(s)::

    git submodule update --init --recursive

Viewport Preview
----------------
BlenderPanda is implemented as a Render Engine, so make sure it is selected from the Render Engine dropdown in Blender's info bar.
To preview a scene in Panda3D, simply switch to a rendered viewport.
Depending on the size of the Blender scene, it may take some time to convert to Panda3D.

Setting up a Project
--------------------
.. note::
	The goal of this section is to discuss just enough about managing a project to get you going with BlenderPanda.
	You can find more information on managing a project in BlenderPanda in the :doc:`Project Mangement documentation <project_management>`.

While some features such as viewport previewing and BAM export are possible without a project, to make full use of BlenderPanda you'll need to set one up.

Your two options are to:

1. Start a new game/project using BlenderPanda
2. Setup a BlenderPanda project from your existing game project


Creating a New Project
^^^^^^^^^^^^^^^^^^^^^^
To create a new project from scratch, click on the Create New Project button in the render properties.

.. image:: images/create_project.png
    :alt: Create New Project button

This brings up Blender's file dialog allowing you to select a folder to create the new project in.
This will generate a handful of files and directories to get you setup quickly.
Assuming a directory called ``new_project`` was select, the following directory structure is created::

	new_project/
	├── assets
	├── game
	│   ├── blenderpanda
	│   │   ├── bpbase.py
	│   │   ├── __init__.py
	│   │   ├── pman_build.py
	│   │   ├── pman.py
	│   │   └── rendermanager.py
	│   └── main.py
	└── .pman

A quick explanation of some of the files:

*.pman*
	An INI file that contains settings for your project.
	This file in the root of your project directory is also how BlenderPanda detects a project.
	BlenderPanda provides a GUI front-end to the settings in this file.

*assets*
	The default directory to place source assets (e.g., blend files, images, etc.) to be converted.
	The location of the assets directory can be modified in ``.pman``.

*game/blenderpanda*
	A module that BlenderPanda uses to hook into your game code to provide features such as auto-building.
	There should be no need to edit the files in this directory.

*game/main.py*
	This is the entry point of your Panda3D application.
	You can do whatever you want with this file, but for the best experience, you should keep the model path changes and the ``blenderpanda`` instantiation.

*game/assets*
	While not initially created, this is the default export directory.
	When building a project, all converted/built files will be put here.
	This file is created automatically as part of the build step and should not be put under version control.

When BlenderPanda detects a project, the render properties are updated:

.. image:: images/project_settings.png

Using an Existing Project
^^^^^^^^^^^^^^^^^^^^^^^^^
TODO

Building and Running the Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The project can be run via the main.py as any normal Panda3D application or the Run Project button in the render properties in Blender.

If you have any assets that need to be converted, the Build Project button will convert all items in the asset directory and place them in the export directory (creating it if need be).
When building a project, a source file in the asset directory will only be converted if it has a newer timestamp than the converted file in the export directory.
In other words, only out-of-date assets are converted.

If auto-building is enabled -- which it is by default -- then the project will be built every time the game is run.
This includes running the game from within Blender via BlenderPanda or running ``main.py`` normally.
The build process is very quick if no assets need to be converted, so auto-building should not hurt iteration times when programming.
However, auto-build is very useful when pulling in new/modified source assets from a version control system.
Therefore, it is recommended to leave auto-building enabled.

