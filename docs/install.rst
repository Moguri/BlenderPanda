Installation
============

Dependencies
------------

In order to use BlenderPanda, you need to satisfy two dependencies:

* Blender (tested with 2.77)
* A Python3 version of the Panda3D SDK

Getting Blender up and running is simple enough.
Just go to `blender.org <https://www.blender.org>`_, download Blender, and run it.

Getting Panda3D running and accessible from Blender is trickier.
First off, the Panda3D build must be built against the Python version that Blender uses (currently Python 3.5).
While there are no official, stable Python 3 builds of Panda3D, there are development SDK builds that will work.
These builds can be found `here <https://www.panda3d.org/download.php?sdk&version=devel>`_.

After the Panda3D SDK has been downloaded and installed, some steps may need to be taken to get Blender to recognize the install.
Blender needs to be able to find three things:

* The panda3d Python package
* The direct Python package (part of Panda3D SDK)
* The Panda3D shared object files (e.g., so, dll)

The first two need to be on the PYTHONPATH that Blender uses.
If Blender is using the system's Python and Panda3D is setup to work from the system Python, then Blender should be able to find everything.
If Blender is using its bundled Python, then you can add a `pth file <https://docs.python.org/3/library/site.html>`_ to Blender's site-packages directory.
The pth file should contain paths to the folder containing the panda3d and direct packages (this might be the same folder).
With the pth file taking care of the Python packages, the shared objects need to be handled next.
On Windows and Mac OS X, Panda3D should be able to automatically find the shared objects.
On Linux, add the directory containing the shared objects to the LD_LIBRARY_PATH.

If everything is setup correctly, ``import panda3d`` should work from Blender's embedded Python console.

Installing the Addon
--------------------

After dependencies are met, it is time to install the addon itself.
GitHub's download zip option does not support git submodules, which are used by BlenderPanda to bring in the `BlenderRealtimeEngineAddon <https://github.com/Kupoman/BlenderRealtimeEngineAddon>`_.
Instead, it is recommended to use `git <https://git-scm.com/>`_ to grab the addon.
From the user addons directory (e.g., ~/.config/blender/2.xx/scripts/addons on Linux) use the following git command::

    git clone --recursive https://github.com/Moguri/BlenderPanda.git

To update to the latestversion of the addon run the following from the addon's directory::

    git update

With the addon repository cloned, the addon should now show up in the addons section of Blender's User Preferences and can be enabled from there.
If all has gone well, a Panda3D RenderEngine should now be available.
If the addon has been enabled, but does not show up in the RenderEngine drop down, check the console for errors.

The mostly likely source of errors is not having Panda3D setup correctly.
If, instead, there is an error about not being able to find brte or a submodule in brte, the git repository is likely missing its submodules.
This can happen if the ``--recursive`` option was not used.
The following git commands should bring in the missing submodule(s)::

    git submodule init
    git submodule update
