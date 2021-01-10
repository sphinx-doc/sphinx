.. c:namespace:: ids_vs_tags2

.. c:struct:: A

   .. c:union:: @B

      .. c:enum:: C

         .. c:enumerator:: D

- :c:enumerator:`struct A.union @B.enum C.D`
- :c:enumerator:`A.union @B.enum C.D`
- :c:enumerator:`struct A.@B.enum C.D`
- :c:enumerator:`struct A.union @B.C.D`
- :c:enumerator:`A.@B.enum C.D`
- :c:enumerator:`A.union @B.C.D`
- :c:enumerator:`struct A.@B.C.D`
- :c:enumerator:`A.@B.C.D`
- :c:enumerator:`struct A.enum C.D`
- :c:enumerator:`A.enum C.D`
- :c:enumerator:`struct A.C.D`
- :c:enumerator:`A.C.D`
