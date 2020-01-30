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
