graphviz
========

.. digraph:: foo
   :caption: caption of graph

   bar -> baz

.. |graph| digraph:: bar

           bar -> baz

Hello |graph| graphviz world

.. digraph:: foo
   :graphviz_dot: neato
   :class: neato_graph

   baz -> qux


.. graphviz:: graph.dot

.. digraph:: bar
   :align: right
   :caption: on *right*

   foo -> bar

.. digraph:: foo
   :align: center

   centered

.. graphviz::
   :align: center

   digraph test {
     foo [label="foo", URL="#graphviz", target="_parent"]
     bar [label="bar", image="./_static/images/test.svg"]
     baz [label="baz", URL="./_static/images/test.svg"]
     foo -> bar -> baz
   }
