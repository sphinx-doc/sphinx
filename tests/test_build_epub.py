"""Test the HTML builder and check output against XPath."""

import os
import subprocess
from subprocess import PIPE, CalledProcessError

import pytest


# check given command is runnable
def runnable(command):
    try:
        subprocess.run(command, stdout=PIPE, stderr=PIPE, check=True)
        return True
    except (OSError, CalledProcessError):
        return False  # command not found or exit with non-zero


@pytest.mark.skipif('DO_EPUBCHECK' not in os.environ,
                    reason='Skipped because DO_EPUBCHECK is not set')
@pytest.mark.sphinx('epub')
def test_run_epubcheck(app):
    app.build()

    epubcheck = os.environ.get('EPUBCHECK_PATH', '/usr/share/java/epubcheck.jar')
    if runnable(['java', '-version']) and os.path.exists(epubcheck):
        try:
            subprocess.run(['java', '-jar', epubcheck, app.outdir / 'SphinxTests.epub'],
                           stdout=PIPE, stderr=PIPE, check=True)
        except CalledProcessError as exc:
            print(exc.stdout.decode('utf-8'))
            print(exc.stderr.decode('utf-8'))
            raise AssertionError('epubcheck exited with return code %s' % exc.returncode)
