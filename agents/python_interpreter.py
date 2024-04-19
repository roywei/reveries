import os
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output


class PythonInterpreter:
    def __init__(self, preset_functions=None):
        self.shell = InteractiveShell.instance()
        self.max_output = int(os.environ.get('PYTHON_INTERPRETER_MAX_OUTPUT', 5000))
        if preset_functions:
            self.run(preset_functions)


    def run(self, code):
        with capture_output() as captured:
            try:
                self.shell.run_cell(code)
                stdout = captured.stdout
                stderr = captured.stderr
            except Exception as e:
                stdout = ""
                stderr = str(e)

        # Combine stdout and stderr
        output = f"STDOUT: {stdout}, STDERR: {stderr}"

        # Truncate output
        if len(output) > self.max_output:
            output = output[:self.max_output]

        return output

