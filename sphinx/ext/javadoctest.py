"""Mimic javadoctest in Sphinx.

The extension automatically execute code snippets and checks their results on Java engine.
"""

import subprocess
from typing import Any, Dict

from sphinx.application import Sphinx
from sphinx.ext.doctest import (
    DocTestBuilder,
    TestcodeDirective,
    TestoutputDirective,
    doctest,
    sphinx,
)
from sphinx.locale import __


class JavaTestcodeDirective(TestcodeDirective):
    def run(self):
        node_list = super().run()
        print("check_node_list")
        print(node_list)
        node_list[0]["language"] = "java"
        return node_list


class JavaDocTestBuilder(DocTestBuilder):
    """
    Runs Java test snippets in the documentation.
    """

    name = "javadoctest"
    epilog = __(
        "Java testing of doctests in the sources finished, look at the "
        "results in %(outdir)s/output.txt.",
    )

    def compile(
        self, code: str, name: str, type: str, flags: Any, dont_inherit: bool,
    ) -> Any:
        if self.config.javadoc_options['flavor'].lower() == 'java':
            stdout_dependency = ''
        elif self.config.javadoc_options['flavor'].lower() == 'java_with_maven':
            # go to project that contains all your Java maven dependencies
            path_java_project = self.config.javadoc_options['path']
            # create list of all Java jar dependencies
            subprocess.check_call(
                [
                    "mvn",
                    "-q",
                    "dependency:build-classpath",
                    "-DincludeTypes=jar",
                    "-Dmdep.outputFile=.cp.tmp",
                    f"-Dversion={self.env.config.version}",
                ],
                cwd=path_java_project,
                text=True,
            )
            if not (path_java_project / ".cp.tmp").exists():
                raise RuntimeError(
                    __("Invalid process to create JShell dependencies library"),
                )
            # get list of all Java jar dependencies
            with open(path_java_project / ".cp.tmp", encoding='utf-8') as f:
                stdout_dependency = f.read()
            if not stdout_dependency:
                raise RuntimeError(
                    __("Invalid process to collect JShell dependencies library"),
                )
        else:
            raise RuntimeError(
                __("Invalid Java flavor to be analyzed"),
            )

        # execute Java testing code thru JShell and read output
        proc_jshell_process = subprocess.Popen(
            ["jshell", "-R--add-opens=java.base/java.nio=ALL-UNNAMED",
             "--class-path", stdout_dependency, "-s", "/dev/stdin"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        out_java, err_java = proc_jshell_process.communicate(code)
        if err_java:
            raise RuntimeError(__("Invalid process to run JShell"))

        # continue with Python logic code to do Java output validation
        output = f"print('''{self.clean_output(out_java)}''')"

        # continue with Sphinx default logic
        return compile(output, name, self.type, flags, dont_inherit)

    def clean_output(self, output: str) -> str:
        if output[-3:] == '-> ':
            output = output[:-3]
        if output[-1:] == '\n':
            output = output[:-1]
        output = (4 * ' ').join(output.split('\t'))
        return output


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_directive("testcode", JavaTestcodeDirective)
    app.add_directive("testoutput", TestoutputDirective)
    app.add_builder(JavaDocTestBuilder)
    # this config value adds to sys.path
    app.add_config_value("doctest_path", [], False)
    app.add_config_value("doctest_test_doctest_blocks", "default", False)
    app.add_config_value("doctest_global_setup", "", False)
    app.add_config_value("doctest_global_cleanup", "", False)
    app.config.add('javadoc_options', {}, True, None)
    app.add_config_value(
        'doctest_default_flags',
        doctest.DONT_ACCEPT_TRUE_FOR_1 | doctest.ELLIPSIS | doctest.IGNORE_EXCEPTION_DETAIL,
        False)
    return {"version": sphinx.__display_version__, "parallel_read_safe": True}
