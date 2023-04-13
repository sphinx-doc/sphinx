"""Mimic javadoctest in Sphinx.

The extension automatically execute code snippets and checks their results on Java engine.
"""
import subprocess
import tempfile
from typing import Any, Dict

from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.ext.doctest import (
    DocTestBuilder,
    TestcodeDirective,
    TestoutputDirective,
    doctest,
    sphinx,
)
from sphinx.locale import __


def validate_java_version():
    """Get current Java version installed/configured on the Operative System.
    """
    try:
        subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise ExtensionError(__('Java error: ' + e.output.decode()))


def validate_maven_version():
    """Get current Maven version installed/configured on the Operative System.
    """
    try:
        subprocess.check_output(['mvn', '-version'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise ExtensionError(__('Maven error: ' + e.output.decode()))


class JavaTestcodeDirective(TestcodeDirective):
    def run(self):
        node_list = super().run()
        node_list[0]['language'] = 'java'
        return node_list


class JavaDocTestBuilder(DocTestBuilder):
    """
    Runs Java test snippets in the documentation.
    """

    name = 'javadoctest'
    epilog = __(
        'Java testing of doctests in the sources finished, look at the '
        'results in %(outdir)s/output.txt.',
    )

    def init(self) -> None:
        super().init()

    def compile(
            self, code: str, name: str, type: str, flags: Any, dont_inherit: bool,
    ) -> Any:
        validate_java_version()
        if self.config.java_doctest_config['flavor'].lower() == 'java':
            stdout_dependency = ''
        elif self.config.java_doctest_config['flavor'].lower() == 'java_with_maven':
            validate_maven_version()
            # go to project that contains all your Java maven dependencies
            path_java_project = self.config.java_doctest_config['path']
            # create a file with the list of all Java jar dependencies
            file_with_all_dependencies = tempfile.NamedTemporaryFile()
            try:
                subprocess.check_output(
                    [
                        'mvn',
                        '-q',
                        'dependency:build-classpath',
                        '-DincludeTypes=jar',
                        f'-Dmdep.outputFile={file_with_all_dependencies.name}',
                        f'-Dversion={self.env.config.version}',
                    ],
                    cwd=path_java_project,
                    text=True,
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as e:
                raise ExtensionError(__('Maven dependency error: ' + e.output))

            # get list of all Java jar dependencies
            with open(file_with_all_dependencies.name, encoding='utf-8') as f:
                stdout_dependency = f.read()
            if not stdout_dependency:
                raise ExtensionError(__('Invalid process to collect JShell dependencies '
                                        'library'),)
        else:
            raise ExtensionError(
                __('Invalid Java flavor option, current options available are: '
                   'java or java_with_maven'),
            )

        # execute Java testing code thru JShell and read output
        proc_jshell_process = subprocess.Popen(
            ['jshell', '-R--add-opens=java.base/java.nio=ALL-UNNAMED',
             '--class-path', stdout_dependency, '-s', '/dev/stdin'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        out_java, err_java = proc_jshell_process.communicate(code)
        if err_java:
            raise ExtensionError(__('Invalid process to run JShell'))

        # continue with Python logic code to do Java output validation
        output = f"print('''{self.clean_output(out_java)}''')"

        # continue with Sphinx default logic
        return compile(output, name, self.type, flags, dont_inherit)

    def clean_output(self, output: str) -> str:
        if output[-3:] == '-> ':
            output = output[:-3]
        if output.endswith('\n'):
            output = output[:-1]
        output = (4 * ' ').join(output.split('\t'))
        return output


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_directive('testcode', JavaTestcodeDirective)
    app.add_directive('testoutput', TestoutputDirective)
    app.add_builder(JavaDocTestBuilder)
    # this config value adds to sys.path
    app.add_config_value('doctest_path', [], False)
    app.add_config_value('doctest_test_doctest_blocks', 'default', False)
    app.add_config_value('doctest_global_setup', '', False)
    app.add_config_value('doctest_global_cleanup', '', False)
    app.add_config_value(
        'doctest_default_flags',
        doctest.DONT_ACCEPT_TRUE_FOR_1 | doctest.ELLIPSIS | doctest.IGNORE_EXCEPTION_DETAIL,
        False)
    app.add_config_value('java_doctest_config', {'flavor': 'java'}, False)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
