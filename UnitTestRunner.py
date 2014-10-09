import os
import re
import sublime
import sublime_plugin
import functools

DEFAULT_TEST_COMMAND = "nosetests "
TEST_DELIMETER = ":"

COMMAND_CHAIN = " ; "
if sublime.platform() == "windows":
    COMMAND_CHAIN = " && "


def Window():
    return sublime.active_window()


class Settings(object):

    def __init__(self):
        self.settings = sublime.load_settings(
            'UnitTestRunner.sublime-settings')

    def __getattr__(self, name):
        if not self.settings.has(name):
            raise AttributeError(name)
        return self.settings.get(name)


class OutputPanel(object):

    def __init__(self, window, settings):
        self.window = window
        self.settings = settings

    def show_color(self, active=True):
        if active:
            self.panel = self.window.get_output_panel('exec')
            self.panel.settings().set('color_scheme', self.settings.theme)
            self.panel.set_syntax_file(self.settings.syntax)


class RunAnUnitTestCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.load_settings()
        self.clean_settings()
        self.prepare_command()
        self.run_command()

    def run_command(self):
        self.output.show_color(self.show_color)
        self.view.window().run_command(
            "exec",
            {
                "cmd": ["bash", "-c", self.command],
                "shell": False,
                "working_dir": self.test_root,
            }
        )
        self.save_test_run(self.command)

    def load_settings(self):
        self.output = OutputPanel(self.view.window(), Settings())
        settings = (
            self.view.window().active_view()
            .settings().get("python_test_runner")
        )
        if settings is None:
            sublime.error_message(
                "Python Test Runner:\nYou must add section 'python_test_runner' into "
                "'settings' section.")
            raise Exception("Cannot run without settings.")

        self.test_root = settings.get(
            'test_root', self.view.window().folders()[0]
        )
        self.test_command = settings.get('test_command', DEFAULT_TEST_COMMAND)
        self.before_test = settings.get('before_test')
        self.after_test = settings.get('after_test')
        self.test_delimeter = settings.get('test_delimeter', TEST_DELIMETER)
        self.show_color = settings.get('show_color', True)

    def clean_settings(self):
        if 'nosetests' in self.test_command:
            if not self.test_command.endswith(' '):
                self.test_command += ' '

    def get_test_path(self):
        abs_file = self.view.file_name()
        rel_path = os.path.relpath(abs_file, self.test_root)
        self.test_path = rel_path.replace('/', '.')
        return self.test_path[:-3]  # remove .py

    def prepare_command(self):
        self.command = self.test_command + self.get_test_path()
        if self.before_test:
            self.command = self.before_test + COMMAND_CHAIN + self.command
        if self.after_test:
            self.command = self.command + COMMAND_CHAIN + self.after_test

    def save_test_run(self, command):
        s = sublime.load_settings("UnitTestRunner.last-run")
        s.set("last_test_run", command)
        sublime.save_settings("UnitTestRunner.last-run")


class RunSeparateUnitTestCommand(RunAnUnitTestCommand):

    def run(self, edit):
        self.load_settings()
        self.clean_settings()
        self.prepare_command()

    def prepare_command(self):
        self.get_test_path()

    def get_test_path(self):
        candidate_test_name = self.test_command
        self.test_name = None

        Window().show_input_panel("Test command to execute", str(candidate_test_name),
                                  functools.partial(self.success), None, None)

    def success(self, testName):
        if testName:
            self.command = testName

        if self.before_test:
            self.command = self.before_test + COMMAND_CHAIN + self.command

        if self.after_test:
            self.command = self.command + COMMAND_CHAIN + self.after_test

        self.run_command()


class RunLastUnitTestCommand(RunAnUnitTestCommand):

    def prepare_command(self):
        s = sublime.load_settings("UnitTestRunner.last-run")
        self.command = s.get("last_test_run")


class TestMethodMatcher(object):

    def find_test_path(self, test_file_content, delimeter=TEST_DELIMETER):
        test_method = self.find_test_method(test_file_content)
        if test_method:
            test_class = self.find_test_class(test_file_content)
            return delimeter + test_class + "." + test_method

    def find_test_method(self, test_file_content):
        match_methods = re.findall(
            r'\s?def\s+(test_\w+)\s?\(', test_file_content)
        if match_methods:
            return match_methods[-1]

    def find_test_class(self, test_file_content):
        match_classes = re.findall(r'\s?class\s+(\w+)\s?\(', test_file_content)
        if match_classes:
            try:
                return [c for c in match_classes if "Test" in c or "test" in c][-1]
            except IndexError:
                return match_classes[-1]
