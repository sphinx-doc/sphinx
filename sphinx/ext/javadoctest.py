"""Mimic javadoctest in Sphinx.

The extension automatically execute code snippets and checks their results on Java engine.
"""
import subprocess
import tempfile
import textwrap

from sphinx.util import logging
from typing import Any, Dict
from docutils import nodes
from docutils.nodes import Element, Node
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.ext.doctest import (
    DocTestBuilder,
    TestCode,
    TestcodeDirective,
    TestGroup,
    TestoutputDirective,
    doctest,
    sphinx, SphinxDocTestRunner,
)
from sphinx.locale import __

logger = logging.getLogger(__name__)

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
            stderr=subprocess.STDOUT,
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
        if output.endswith('\n-> '):
            output = output[:-4]
        output = (4 * ' ').join(output.split('\t'))
        return output

    def test_doc(self, docname: str, doctree: Node) -> None:
        groups: dict[str, TestGroup] = {}
        add_to_all_groups = []
        self.setup_runner = SphinxDocTestRunner(verbose=False,
                                                optionflags=self.opt)
        self.test_runner = SphinxDocTestRunner(verbose=False,
                                               optionflags=self.opt)
        self.cleanup_runner = SphinxDocTestRunner(verbose=False,
                                                  optionflags=self.opt)

        self.test_runner._fakeout = self.setup_runner._fakeout  # type: ignore
        self.cleanup_runner._fakeout = self.setup_runner._fakeout  # type: ignore

        if self.config.doctest_test_doctest_blocks:
            def condition(node: Node) -> bool:
                return (isinstance(node, (nodes.literal_block, nodes.comment)) and
                        'testnodetype' in node) or \
                    isinstance(node, nodes.doctest_block)
        else:
            def condition(node: Node) -> bool:
                return isinstance(node, (nodes.literal_block, nodes.comment)) \
                    and 'testnodetype' in node
        for node in doctree.findall(condition):  # type: Element
            if self.skipped(node):
                continue

            source = node['test'] if 'test' in node else node.astext()
            filename = self.get_filename_for_node(node, docname)
            line_number = self.get_line_number(node)
            if not source:
                logger.warning(__('no code/output in %s block at %s:%s'),
                               node.get('testnodetype', 'doctest'),
                               filename, line_number)
            code = TestCode(source, type=node.get('testnodetype', 'doctest'),
                            filename=filename, lineno=line_number,
                            options=node.get('options'))
            node_groups = node.get('groups', ['default'])
            if '*' in node_groups:
                add_to_all_groups.append(code)
                continue
            for groupname in node_groups:
                if groupname not in groups:
                    groups[groupname] = TestGroup(groupname)
                groups[groupname].add_code(code)
        for code in add_to_all_groups:
            for group in groups.values():
                group.add_code(code)
        if self.config.doctest_global_setup:
            code = TestCode(self.config.doctest_global_setup,
                            'testsetup', filename=None, lineno=0)
            for group in groups.values():
                group.add_code(code, prepend=True)
        if self.config.doctest_global_cleanup:
            code = TestCode(self.config.doctest_global_cleanup,
                            'testcleanup', filename=None, lineno=0)
            for group in groups.values():
                group.add_code(code)
        if not groups:
            return

        self._out('\nDocument: %s\n----------%s\n' %
                  (docname, '-' * len(docname)))
        for group in groups.values():
            self.test_group(group)
        # Separately count results from setup code
        res_f, res_t = self.setup_runner.summarize(self._out, verbose=False)
        self.setup_failures += res_f
        self.setup_tries += res_t
        if self.test_runner.tries:
            res_f, res_t = self.test_runner.summarize(self._out, verbose=True)
            self.total_failures += res_f
            self.total_tries += res_t
        if self.cleanup_runner.tries:
            res_f, res_t = self.cleanup_runner.summarize(self._out,
                                                         verbose=True)
            self.cleanup_failures += res_f
            self.cleanup_tries += res_t

class TestGroup(TestGroup):
    def add_code(self, code: TestCode, prepend: bool = False) -> None:
        if code.type == 'testsetup':
            if prepend:
                self.setup.insert(0, code)
            else:
                self.setup.append(code)
        elif code.type == 'testcleanup':
            self.cleanup.append(code)
        elif code.type == 'doctest':
            self.tests.append([code])
        elif code.type == 'testcode':
            self.tests.append([code, None])
        elif code.type == 'testoutput':
            if self.tests and len(self.tests[-1]) == 2:
                self.tests[-1][1] = code
        elif code.type == 'javatestcode':
            self.tests.append([code, None])
        elif code.type == 'javatestoutput':
            if self.tests and len(self.tests[-1]) == 2:
                self.tests[-1][1] = code
        else:
            raise RuntimeError(__('invalid TestCode type'))

def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_directive('javatestcode', JavaTestcodeDirective)
    app.add_directive('javatestoutput', TestoutputDirective)
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
