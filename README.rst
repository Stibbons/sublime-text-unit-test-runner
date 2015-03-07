***********************************
Unit Test Runner for Sublime Text 3
***********************************

Windows
=======

Windows makes things a bit more complex

For example, if I want to run a command in a python virtualenv, I cannot source a file and
then launch my command.

In the following example, I have an entry point in my project named "launcher.bat" that
allows me to run any command inside the virtual env.

I simply set this into the ``before_test`` section of my project settings

Example:

::

    "python_unit_test_runner": {
        "project_roots": "D:\\path\\to\\project",
        "use_project_root": true,
        "before_test": "install\\launcher.bat D:\\path\\to\\workdir",
        "test_command": "trial project_name.module",
        "show_color": true
    }
