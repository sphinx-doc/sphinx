.. default-domain:: cpp

.. namespace:: multi_decl_lookup

.. function:: void f1(int a)
              void f1(double b)

   - a: :var:`a`
   - b: :var:`b`

.. function:: template<typename T> void f2(int a)
              template<typename U> void f2(double b)

   - T: :type:`T`
   - U: :type:`U`


.. class:: template<typename T> A
           template<typename U> B

   .. function:: void f3()

      - T: :type:`T`
      - U: :type:`U`
