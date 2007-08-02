:mod:`email`: Examples
----------------------

Here are a few examples of how to use the :mod:`email` package to read, write,
and send simple email messages, as well as more complex MIME messages.

First, let's see how to create and send a simple text message:


.. include:: ../includes/email-simple.py
   :literal:

Here's an example of how to send a MIME message containing a bunch of family
pictures that may be residing in a directory:


.. include:: ../includes/email-mime.py
   :literal:

Here's an example of how to send the entire contents of a directory as an email
message:  [#]_


.. include:: ../includes/email-dir.py
   :literal:

And finally, here's an example of how to unpack a MIME message like the one
above, into a directory of files:


.. include:: ../includes/email-unpack.py
   :literal:


.. rubric:: Footnotes

.. [#] Thanks to Matthew Dixon Cowles for the original inspiration and examples.

