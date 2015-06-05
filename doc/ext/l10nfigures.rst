:mod:`sphinx.ext.l10nfigures` -- Look for localized version of the figures
==========================================================================

.. module:: sphinx.ext.l10nfigures
   :synopsis: Allow figures to be localized by looking for language-specific
              files.

Once enabled, this extension allows to switch figures for different
languages. It works by looking for the :rst:dir:`figure` directive in the
source, and for each of them, it looks for a language-specific picture file.

The name of the file that is being looked for is constructed as follow
:samp:`filename-{lang}.ext`. If the localized files are not found, the
original one will be used. For instance, for a file name ``picture.png``, when
generated for the french language, the file ``picture-fr.png`` will be
searched, for english, the file ``picture-en.png`` will be searched.


