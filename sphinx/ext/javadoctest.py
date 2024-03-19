"""Mimic javadoctest in Sphinx.

The extension automatically execute code snippets and checks their results on Java engine.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from typing import TYPE_CHECKING, Any

from docutils import nodes
from docutils.parsers.rst import directives
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

from sphinx.errors import ExtensionError
from sphinx.ext.doctest import (
    DocTestBuilder,
    SphinxDocTestRunner,
    TestCode,
    TestDirective,
    TestGroup,
    doctest,
    sphinx,
)
from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from docutils.nodes import Element, Node, TextElement

    from sphinx.application import Sphinx
    from sphinx.util.typing import OptionSpec

logger = logging.getLogger(__name__)

jshell_blankline_re = re.compile(r'^\s*System.out.println\s*', re.MULTILINE)
blankline_re = re.compile(r'^\s*<BLANKLINE>', re.MULTILINE)
javadoctestopt_re = re.compile(r'#\s*javadoctest:.+$', re.MULTILINE)


def is_allowed_version(spec: str, version: str) -> bool:
    """Check `spec` satisfies `version` or not.
    """
    return Version(version) in SpecifierSet(spec)


def get_java_version() -> Any:
    try:
        java_version = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
        logger.debug("Java version configured: %s", java_version)
        return re.search(r'\"(\d+\.\d+\.\d).*\"',
                         java_version.decode("utf-8")).groups()[0]  # type: ignore[union-attr]
    except subprocess.CalledProcessError as exc:
        raise ExtensionError(__('Java version error: ' + exc.output.decode)) from exc


def validate_java_version():
    if get_java_version().startswith('1.8.'):
        raise ExtensionError(__('Java error: Minimum Java version supported is 11.0+')) \
            from None


def validate_maven_version():
    try:
        maven_version = subprocess.check_output(['mvn', '-version'], stderr=subprocess.STDOUT)
        logger.debug("Java version configured: %s", maven_version)
    except subprocess.CalledProcessError as exc:
        raise ExtensionError(__('Maven version error: ' + exc.output.decode())) from exc


class JavaTestDirective(TestDirective):
    """
    Base class for javadoctest-related directives.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self) -> list[Node]:
        # use ordinary docutils nodes for test code: they get special attributes
        # so that our builder recognizes them, and the other builders are happy.
        code = '\n'.join(self.content)
        test = None
        if self.name == 'javadoctest':
            if '<BLANKLINE>' in code:
                # convert <BLANKLINE>s to ordinary blank lines for presentation
                test = code
                code = blankline_re.sub('', code)
            if javadoctestopt_re.search(code) and 'no-trim-doctest-flags' not in self.options:
                if not test:
                    test = code
                code = javadoctestopt_re.sub('', code)
        nodetype: type[TextElement] = nodes.literal_block
        if self.name in ('javatestsetup', 'javatestcleanup') or 'hide' in self.options:
            nodetype = nodes.comment
        if self.arguments:
            groups = [x.strip() for x in self.arguments[0].split(',')]
        else:
            groups = ['default']
        node = nodetype(code, code, testnodetype=self.name, groups=groups)
        self.set_source_info(node)
        if test is not None:
            # only save if it differs from code
            node['test'] = test
        if self.name in ('javadoctest', 'javatestcode'):
            node['language'] = 'java'
        elif self.name == 'javatestoutput':
            # don't try to highlight output
            node['language'] = 'none'
        node['options'] = {}
        if self.name in ('javadoctest', 'javatestoutput') and 'options' in self.options:
            # parse doctest-like output comparison flags
            option_strings = self.options['options'].replace(',', ' ').split()
            for option in option_strings:
                prefix, option_name = option[0], option[1:]
                if prefix not in '+-':
                    self.state.document.reporter.warning(
                        __("missing '+' or '-' in '%s' option.") % option,
                        line=self.lineno)
                    continue
                if option_name not in doctest.OPTIONFLAGS_BY_NAME:
                    self.state.document.reporter.warning(
                        __("'%s' is not a valid option.") % option_name,
                        line=self.lineno)
                    continue
                flag = doctest.OPTIONFLAGS_BY_NAME[option[1:]]
                node['options'][flag] = (option[0] == '+')
        if self.name in ('javadoctest', 'javatestcode', 'javatestoutput') \
                and 'javaversion' in self.options:
            try:
                spec = self.options['javaversion']
                java_version = get_java_version()
                if not is_allowed_version(spec, java_version):
                    flag = doctest.OPTIONFLAGS_BY_NAME['SKIP']
                    node['options'][flag] = True  # Skip the test
            except InvalidSpecifier:
                self.state.document.reporter.warning(
                    __("'%s' is not a valid javaversion option") % spec,
                    line=self.lineno)
        if 'skipif' in self.options:
            node['skipif'] = self.options['skipif']
        if 'trim-doctest-flags' in self.options:
            node['trim_flags'] = True
        elif 'no-trim-doctest-flags' in self.options:
            node['trim_flags'] = False
        return [node]


class JavaTestsetupDirective(JavaTestDirective):
    option_spec: OptionSpec = {
        'skipif': directives.unchanged_required,
    }


class JavaTestcleanupDirective(JavaTestDirective):
    option_spec: OptionSpec = {
        'skipif': directives.unchanged_required,
    }


class JavaDoctestDirective(JavaTestDirective):
    option_spec: OptionSpec = {
        'hide': directives.flag,
        'no-trim-doctest-flags': directives.flag,
        'options': directives.unchanged,
        'javaversion': directives.unchanged_required,
        'skipif': directives.unchanged_required,
        'trim-doctest-flags': directives.flag,
    }


class JavaTestcodeDirective(JavaTestDirective):
    option_spec: OptionSpec = {
        'hide': directives.flag,
        'no-trim-doctest-flags': directives.flag,
        'javaversion': directives.unchanged_required,
        'skipif': directives.unchanged_required,
        'trim-doctest-flags': directives.flag,
    }


class JavaTestoutputDirective(JavaTestDirective):
    option_spec: OptionSpec = {
        'hide': directives.flag,
        'no-trim-doctest-flags': directives.flag,
        'options': directives.unchanged,
        'javaversion': directives.unchanged_required,
        'skipif': directives.unchanged_required,
        'trim-doctest-flags': directives.flag,
    }


parser = doctest.DocTestParser()


# class JavaTestcodeDirective(TestcodeDirective):
#     def run(self):
#         node_list = super().run()
#         node_list[0]['language'] = 'java'
#         return node_list

class JavaDocTestBuilder(DocTestBuilder):
    """
    Runs Java test snippets in the documentation.
    """
    name = 'javadoctest'
    epilog = __(
        'Java testing of doctests in the sources finished, look at the '
        'results in %(outdir)s/output.txt.',
    )

    def compile(
            self, code: str, name: str, type: str, flags: Any, dont_inherit: bool,
    ) -> Any:
        """
        Runs Java test snippets in the documentation.
        """
        validate_java_version()
        if self.config.javadoctest_config['flavor'].lower() == 'java':
            stdout_dependency = ''
        elif self.config.javadoctest_config['flavor'].lower() == 'java_with_maven':
            validate_maven_version()
            path_java_project = self.config.javadoctest_config['path']
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
            except subprocess.CalledProcessError as exc:
                raise ExtensionError(__('Maven dependency error: ' + exc.output)) from exc

            with open(file_with_all_dependencies.name, encoding='utf-8') as f:
                stdout_dependency = f.read()
            if not stdout_dependency:
                raise RuntimeError(__('Invalid process to collect JShell'
                                      ' dependencies library'))
        else:
            raise ExtensionError(
                __('Invalid Java flavor option, current options available are: '
                   'java or java_with_maven'),
            )

        proc_jshell_process = subprocess.Popen(
            ['jshell', '-R--add-opens=java.base/java.nio=ALL-UNNAMED',
             '--class-path', stdout_dependency, '-s', '/dev/stdin', '--startup', 'PRINTING'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        # in order not to have problems with: <BLANKLINE>
        code = jshell_blankline_re.sub('System.out.print', code)
        out_java, err_java = proc_jshell_process.communicate(code)
        if err_java:
            raise ExtensionError(__('Invalid process to run JShell. '
                                    'Error message: ' + err_java))
        output = f"print('''{self.clean_output(out_java)}''')"
        # continue with Sphinx default logic
        return compile(output, name, self.type, flags, dont_inherit)

    def test_group(self, group: TestGroup) -> None:
        ns: dict = {}

        # get setup java cde
        def run_setup(testcodes: list[TestCode]) -> str:
            setup_cleanup_java_code = ""
            for testcode in testcodes:
                setup_cleanup_java_code += testcode.code + '\n'

            return setup_cleanup_java_code

        def run_cleanup(runner: Any, testcodes: list[TestCode], what: Any) -> bool:
            examples = []
            for testcode in testcodes:
                # override from '' to '<BLANKLINE>'
                example = doctest.Example(testcode.code, '<BLANKLINE>', lineno=testcode.lineno)
                examples.append(example)
            if not examples:
                return True
            # simulate a doctest with the code
            sim_doctest = doctest.DocTest(examples, {},
                                          f'{group.name} ({what} code)',
                                          testcodes[0].filename, 0, None)
            sim_doctest.globs = ns
            old_f = runner.failures
            self.type = 'exec'  # the snippet may contain multiple statements
            runner.run(sim_doctest, out=self._warn_out, clear_globs=False)
            if runner.failures > old_f:
                return False
            return True

        setup_java_code = run_setup(group.setup)
        # run the tests
        for code in group.tests:
            if len(code) == 1:
                # ordinary doctests (code/output interleaved)
                try:
                    test = parser.get_doctest(setup_java_code + code[0].code, {}, group.name,
                                              code[0].filename, code[0].lineno)
                except Exception:
                    logger.warning(__('ignoring invalid doctest code: %r'), setup_java_code
                                   + code[0].code, location=(code[0].filename, code[0].lineno))
                    continue
                if not test.examples:
                    continue
                for example in test.examples:
                    # apply directive's comparison options
                    new_opt = code[0].options.copy()
                    new_opt.update(example.options)
                    example.options = new_opt
                self.type = 'single'  # as for ordinary doctests
            else:
                # testcode and output separate
                output = code[1].code if code[1] else ''
                options = code[1].options if code[1] else {}
                # disable <BLANKLINE> processing as it is not needed
                options[doctest.DONT_ACCEPT_BLANKLINE] = True
                # find out if we're testing an exception
                m = parser._EXCEPTION_RE.match(output)  # type: ignore[attr-defined]
                if m:
                    exc_msg = m.group('msg')
                else:
                    exc_msg = None
                example = doctest.Example(setup_java_code + code[0].code, output,
                                          exc_msg=exc_msg, lineno=code[0].lineno,
                                          options=options)
                test = doctest.DocTest([example], {}, group.name,
                                       code[0].filename, code[0].lineno, None)
                self.type = 'exec'  # multiple statements again
            # DocTest.__init__ copies the globs namespace, which we don't want
            test.globs = ns
            # also don't clear the globs namespace after running the doctest
            self.test_runner.run(test, out=self._warn_out, clear_globs=False)

        # run the cleanup
        run_cleanup(self.cleanup_runner, group.cleanup, 'cleanup')

    def skipped(self, node: Element) -> bool:
        if 'skipif' not in node:
            return False
        else:
            condition = node['skipif']
            out_java = "false"
            if self.config.javadoctest_global_setup:
                proc_jshell_process = subprocess.Popen(
                    ['jshell', '-s', '/dev/stdin'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                )
                code = self.config.javadoctest_global_setup.strip() \
                    + 'System.out.print(' + condition + ');'
                out_java, err_java = proc_jshell_process.communicate(code)
                if err_java:
                    raise ExtensionError(__('Invalid process to run JShell. '
                                            'Global Setup for Skip If.'))
            should_skip = self.clean_output(out_java) == "true"
            if self.config.javadoctest_global_cleanup:
                proc_jshell_process = subprocess.Popen(
                    ['jshell', '-s', '/dev/stdin'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                )
                code = self.config.javadoctest_global_cleanup.strip()
                out_java, err_java = proc_jshell_process.communicate(code)
                if err_java:
                    raise ExtensionError(__('Invalid process to run JShell. Global Cleanup.'))
            return should_skip

    def clean_output(self, output: str) -> str:
        # clean JShell silent return
        clean = 0
        if output.endswith('\n-> '):
            clean = 4
            output = output[:-clean]
        elif output.endswith('-> '):
            clean = 3
            output = output[:-clean]
        output = (4 * ' ').join(output.split('\t'))
        return output

    def test_doc(self, docname: str, doctree: Node) -> None:
        """
        Override test_doc to support new directives such as: javatestcode, javatestoutput
        """
        groups: dict[str, JavaTestGroup] = {}
        add_to_all_groups = []
        self.setup_runner = SphinxDocTestRunner(verbose=False,
                                                optionflags=self.opt)
        self.test_runner = SphinxDocTestRunner(verbose=False,
                                               optionflags=self.opt)
        self.cleanup_runner = SphinxDocTestRunner(verbose=False,
                                                  optionflags=self.opt)

        self.test_runner._fakeout = self.setup_runner._fakeout  # type: ignore[attr-defined]
        self.cleanup_runner._fakeout = self.setup_runner._fakeout  # type: ignore[attr-defined]

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
                               node.get('testnodetype', 'javadoctest'),
                               filename, line_number)
            code = TestCode(source, type=node.get('testnodetype', 'javadoctest'),
                            filename=filename, lineno=line_number,
                            options=node.get('options'))
            node_groups = node.get('groups', ['default'])
            if '*' in node_groups:
                add_to_all_groups.append(code)
                continue
            for groupname in node_groups:
                if groupname not in groups:
                    groups[groupname] = JavaTestGroup(groupname)
                groups[groupname].add_code(code)
        for code in add_to_all_groups:
            for group in groups.values():
                group.add_code(code)
        if self.config.javadoctest_global_setup:
            code = TestCode(self.config.javadoctest_global_setup,
                            'javatestsetup', filename='<global_cleanup>', lineno=0)
            for group in groups.values():
                group.add_code(code, prepend=True)
        if self.config.javadoctest_global_cleanup:
            code = TestCode(self.config.javadoctest_global_cleanup,
                            'javatestcleanup', filename='<global_cleanup>', lineno=0)
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


class JavaTestGroup(TestGroup):
    def add_code(self, code: TestCode, prepend: bool = False) -> None:
        """
        To offer support for Java directives
        """
        if code.type == 'javatestsetup':
            if prepend:
                self.setup.insert(0, code)
            else:
                self.setup.append(code)
        elif code.type == 'javatestcleanup':
            self.cleanup.append(code)
        elif code.type == 'javadoctest':
            self.tests.append([code])
        elif code.type == 'javatestcode':
            self.tests.append((code, None))
        elif code.type == 'javatestoutput':
            if self.tests:
                latest_test = self.tests[-1]
                if len(latest_test) == 2:
                    self.tests[-1] = [latest_test[0], code]
        else:
            raise RuntimeError(__('invalid TestCode type: ' + code.type))


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive('javatestsetup', JavaTestsetupDirective)
    app.add_directive('javatestcleanup', JavaTestcleanupDirective)
    app.add_directive('javadoctest', JavaDoctestDirective)
    app.add_directive('javatestcode', JavaTestcodeDirective)
    app.add_directive('javatestoutput', JavaTestoutputDirective)
    app.add_builder(JavaDocTestBuilder)
    # this config value adds to sys.path
    app.add_config_value('javadoctest_config', {'flavor': 'java'}, False)
    app.add_config_value('javadoctest_global_setup', '', False)
    app.add_config_value('javadoctest_global_cleanup', '', False)
    app.add_config_value(
        'doctest_default_flags',
        doctest.DONT_ACCEPT_TRUE_FOR_1 | doctest.ELLIPSIS | doctest.IGNORE_EXCEPTION_DETAIL,
        False)
    app.add_config_value('doctest_path', [], False)
    app.add_config_value('doctest_test_doctest_blocks', 'default', False)

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
