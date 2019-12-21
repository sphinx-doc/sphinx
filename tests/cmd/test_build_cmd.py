# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test the :module:`sphinx.cmd.build` module.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from unittest import mock

from sphinx.cmd.build import main


@mock.patch('os.path.isfile', new=mock.Mock(return_value=True))
@mock.patch('sphinx.cmd.build.Sphinx')
def test_posargs_full(mock_sphinx):
    """Validate behavior with the full complement of posargs."""
    args = ['srcdir', 'outdir', 'file_a', 'file_b', 'file_c']
    main(args)

    mock_sphinx.assert_called_once_with(
        args[0], args[0], args[1], os.path.join(args[1], '.doctrees'),
        mock.ANY, mock.ANY, mock.ANY, mock.ANY, mock.ANY, mock.ANY, mock.ANY,
        mock.ANY, mock.ANY, mock.ANY)
    mock_sphinx.return_value.build.assert_called_once_with(False, args[2:])


@mock.patch('sphinx.cmd.build.Sphinx')
def test_posargs_no_filenames(mock_sphinx):
    """Validate behavior with the source and output dir posarg."""
    args = ['srcdir', 'outdir']
    main(args)

    mock_sphinx.assert_called_once_with(
        args[0], args[0], args[1], os.path.join(args[1], '.doctrees'),
        mock.ANY, mock.ANY, mock.ANY, mock.ANY, mock.ANY, mock.ANY, mock.ANY,
        mock.ANY, mock.ANY, mock.ANY)
    mock_sphinx.return_value.build.assert_called_once_with(False, [])


@mock.patch('sphinx.cmd.build.Sphinx')
def test_posargs_no_outputdir(mock_sphinx):
    """Validate behavior with only the source dir posarg."""
    args = ['srcdir']
    main(args)

    mock_sphinx.assert_called_once_with(
        args[0], args[0], None, None, mock.ANY, mock.ANY, mock.ANY, mock.ANY,
        mock.ANY, mock.ANY, mock.ANY, mock.ANY, mock.ANY, mock.ANY)
    mock_sphinx.return_value.build.assert_called_once_with(False, [])
