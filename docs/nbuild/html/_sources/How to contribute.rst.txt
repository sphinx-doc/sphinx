How to contribute
=================

If you want to contribute to the documentation, either download or clone this
repository: https://github.com/VirtualDataLab/smobsc
and then acess the "docs" directory. There you will find an index.rst file. This
is basically where you see the main structure of the documentation with all the
headers, subheaders etc. If you want to link to a new section, you have to add
it under toctree. When building the documentation sphinx will go through the
sections under toctree and look for .rst files with the same names in the docs
directory. Once you've added the section in the index.rst file and added the
corresponding .rst file in the docs directory, you can build the html with
"make html".

