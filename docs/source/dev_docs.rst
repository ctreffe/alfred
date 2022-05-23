Documentation Guidelines
================================

Generally, alfred3 adheres to `Google Style docstrings`_, with a few
customizations. Here, we note only the deviations from Google Style.

Useful resources for writing docstrings concern directives_
(special commands, e.g. for creating notes or warnings),
`cross-referencing`_ (i.e. links within the documentation), and a
general `ReStructured Text cheat sheet`_. The creation of tables can be
most convenient via `csv tables`_.

Here's the summary:

1. Put the summary sentence on a new line.
2. Document class attributes where they are defined.
3. Document instance attributes in their getter property.
4. Let methods inherit docstrings and leave a note on the inheritance at
   the inherited method.
5. Use the :func:`.inherit_kwargs` decorator to share argument
   documentation between child and parent classes.
6. **Write examples**!
7. Use type annotations.

One-Sentence summary
--------------------

The one-sentence summary of a docstring should start on its own, new
line instead of being on the same line as the three opening quotes.
This improves readability::

    class Example:
        """
        One sentence summary

        Extended summary can be placed here.
        """

        pass

Class and instance attributes
-----------------------------

Class attributes are documented where they are defined,
by placing short descriptions starting with ``#:`` directly above
their definition. This is inspired by Flask's documentation and is
done for two reasons:

1) It works with Sphinx's automatic layout

2) The docstrings are available directly where the attribute is defined.

Instance attributes *that are part of the public API* are documented by
phrasing them as *properties* and writing a docstring in the getter
method. It is good practice to document the returned type with the
first word, followed by a colon (see example).


Example::

    class Example:

        #: This is a short description of a class attribute
        class_attribute: str = "value"

        def __init__(self, inst_attr: str):

            self._inst_attr: str = inst_attr # documented in getter method

        @property
        def inst_attr(self):
            """
            str: Documentation of instance attribute.
            """
            return self._inst_attr


Docstrings of inherited methods
-------------------------------

(Quoted in parts from matplotlib_ documentation) If a subclass
overrides a method but does not change the semantics, we can reuse the
parent docstring for the method of the child class, or tell sphinx not
to add it to the classes own documentation.

*Reusing the parent docstring*: Python does this automatically, if
the subclass method does not have a docstring. Use a plain comment
``# docstring`` inherited to denote the intention to reuse the parent
docstring. That way we do not accidentially create a docstring in the
future. Example::

    class A:
          def foo():
              """The parent docstring."""
              pass

    class B(A):
        def foo():
            # docstring inherited
            pass


Sharing docstrings between classes
-----------------------------------

To enable easy sharing of argument docstrings, we have created a
specialized decorator:

.. autosummary::
    :recursive:
    :toctree: generated
    :template: autosummary/method.rst
    :nosignatures:

    ~alfred3._helper.inherit_kwargs


Writing Examples
----------------

Examples are one of the most important parts of a docstring. Never
forgo writing an example lightly!

Examples in docstrings, besides illustrating the usage of the
function or method, must be valid Python code, that can be copied
and run by users. Comments describing the examples can be added.

Alfred3 should be imported with the statement ``import alfred3 as al``
at the beginning of the example. If any other packages are used, they
should be imported explicitly aswell.

Examples should use minimal alfred experiments written in the object-
oriented style, that is by adding pages/section by deriving new classes
and using the :meth:`.Experiment.member` decorator. Unless the example
requires a different hook, elements (pages) should be added to pages
(sections) in the ``on_exp_access`` hook::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class Example(al.Page):

        def on_exp_access(self):
            self += al.Text("Example text")


Codeblocks can be created simply by ending a line with a double-colon
(``::``). Example::

    This is ordinary text::

        # this is python code
        import alfred3 as al
        exp = al.Experiment()


Using type annotations
----------------------

It's very useful to know the type of function arguments and returned
values, which is why we love type annotations. Here's an example::

    def example_function(arg1: str, arg2: str = "default") -> str:
        return arg1 + arg2

The parts ``arg1: str`` and ``arg2: str = "default"`` are annotated
function arguments. The part ``-> str`` specifies the function's return
type. For more details on how to use type annotations, refer to the
:mod:`typing` module documentation.


Docstring sections
------------------

The docstrings can have the following sections in the following order
(heavily quoting the pandas_ docstring guidelines):

.. csv-table::
   :header: "Section Name", "Heading", "Description"
   :widths: 25, 15,  60
   :width: 100%

   1 **Short summary**,   \-   ,   "A concise one-line summary."
   2 **Extended summary**, \-  ,   "Provides details on what the function does."
   3 **Arguments**, Args:    ,   "The details of the function arguments."
   4 **Returns**,   Returns: ,   "Return value documentation. *Yields* for generators."
   5 **See Also**,  See Also: ,  "Informs users about related alfred3 functionality."
   6 **Notes**,     Notes:   ,   "Optional section for technical and implementation details."
   7 **Examples**,  Examples:,   "Examples, illustrating function usage. **Very important**."

.. _Google Style docstrings: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
.. _pandas: https://pandas.pydata.org/pandas-docs/stable/development/contributing_docstring.html
.. _directives: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html
.. _cross-referencing: https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#cross-referencing-syntax
.. _ReStructured Text cheat sheet: https://github.com/ralsina/rst-cheatsheet/blob/master/rst-cheatsheet.rst
.. _csv tables: https://docutils.sourceforge.io/docs/ref/rst/directives.html#csv-table
.. _matplotlib: https://matplotlib.org/3.1.1/devel/documenting_mpl.html#inheriting-docstrings
