Test Java With Third Dependencies Handled by Maven
==================================================

In case we need to test documentation for projects that consume Java native libraries and
Third party Java dependencies, then, is needed to configure/add these dependencies thru a
dependency management suchs as Maven/Gradle, in this case initially we are offering support
for Maven.

In this case is needed to define by `conf.py` a flavor with `java_with_maven`, and also define
where is your maven project that contains third dependencies thru an absolute `path`.

Java Guava Example
------------------

.. javatestcode::

    import java.util.List;
    import com.google.common.collect.Lists;
    import com.google.common.primitives.Ints;

    List<Integer> theList = Ints.asList(1, 2, 3, 4, 5);
    List<Integer> countDown = Lists.reverse(theList);
    System.out.println(countDown);

.. javatestoutput::

    [5, 4, 3, 2, 1]