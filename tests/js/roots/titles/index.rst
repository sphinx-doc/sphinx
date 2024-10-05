Main Page
=========

This is the main page of the ``titles`` test project.

In particular, this test project is intended to demonstrate how Sphinx
can handle scoring of query matches against document titles and subsection
heading titles relative to other document matches such as terms found within
document text and object names extracted from code.

Relevance
---------

In the context of search engines, we can say that a document is **relevant**
to a user's query when it contains information that seems likely to help them
find an answer to a question they're asking, or to improve their knowledge of
the subject area they're researching.

.. automodule:: relevance
   :members:

Result Scoring
--------------

Many search engines assign a numeric score to documents during retrieval of
results - and this score is often used to determine the order in which they
will be presented to the user.

For example, if a user issues a query for a two words, then documents that
contain both of the words would typically be scored more highly than documents
which only contain one of them.

By evaluating search results and collecting user feedback over time, we can
attempt to align document :index:`!scoring` with :index:`relevance`.
