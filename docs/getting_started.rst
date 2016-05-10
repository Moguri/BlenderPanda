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

Previewing
----------
BlenderPanda is implemented as a Render Engine, so make sure it is selected from the Render Engine dropdown in Blender's info bar.
To preview a scene in Panda3D, simply switch to a rendered viewport.
Depending on the size of the Blender scene, it may take some time to convert to Panda3D.

Starting a Project
------------------
This section aims to discuss just enough about managing a project to get you going with BlenderPanda.
You can find more information on managing a project in BlenderPanda in the :doc:`Project Mangement section <project_management>`.

