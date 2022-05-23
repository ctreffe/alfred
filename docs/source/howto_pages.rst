How to use pages
================

A page serves as the organizing container (and the canvas) for presenting
elements and collecting user inputs. They receive elements and are
themselves appended to either a section or the experiment directly
(which will append the page to the experiment's basic content section).

There are two approaches to writing a page:

1. Append an instance of a page directly to the experiment
   (or a section). We call this style the *instance style* of writing a
   page. It is a little easier to start with and can offer an especially
   clean syntax for short pages.

2. Use one of the base classes provided by alfred3
   to derive a new page. This the more powerful and flexible approach
   to writing a page. We call it the *class style*.

How to write a page in instance style
-------------------------------------

In instance style, you basically add a page directly to the experiment
using the augmented assignment operator ``+=``.
You define its title, name, and other arguments in the instantiation
call::

    import alfred3 as al
    exp = al.Experiment()

    exp += al.Page(title="Example page", name="example_page")

You can then add elements to the page::

    exp.example_page += al.TextEntry(toplab="Text entry", name="el1")

This style is quite easy to learn and understand, which is its main
advantage. The main disadvantage is that you have no access to the
page's hooks - and these hooks are what reveals alfred's greatest
strengths.

The instance style is used when adding pages to a section in one of the
section's hooks - for example, if you want to create a large number of
similar pages in a for-loop. In this case, you have the simplicity of the
instance style and the power of the class style combined.

.. _page-class-style:

How to write a page in class style
----------------------------------

In class style, you derive a new page class for every page
that is added to the experiment. We use the :meth:`.Experiment.member`
decorator for this purpose::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class ExamplePage(al.Page):
        title = "Example page"

As you see in the example, you can define the *title* as a class
attribute in this case. This works for most other initialization
arguments aswell (the documentation of each arguments states whether
it can be defined as a class attribute).

You do not need to define the name of a page written in class style
as a separate argument - alfred will simply use the class name (in this
case *ExamplePage* as the page's name).

Elements are added to a class-style page by defining one of the hook
methods (see :ref:`hooks-how-to`) and adding elements with the
augmented assignment operator ``+=``. In this case, we use the
:meth:`.Page.on_exp_access` hook, which gives us access to the experiment
session, but not the values of previous sessions::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class ExamplePage(al.Page):
        title = "Example page"

        def on_exp_access(self):
            self += al.TextEntry(toplab="Text entry", name="el1")


Now, the method we have shown so far only adds sections to alfred's most
basic section, which is named *_content*. You might ask a very reasonable
question: **How do we add a page to a custom section in class style?**.
Here's how - you simply set the argument *of_section* in the decorator
*@exp.member* to the name of the section::

    import alfred3 as al
    exp = al.Experiment()

    exp += al.OnlyForwardSection(name="main")

    @exp.member(of_section="main")
    class ExamplePage(al.Page):
        title = "Example page"

        def on_exp_access(self):
            self += al.TextEntry(toplab="Text entry", name="el1")


.. note::
    Documentation on hooks (as well as a comprehensive list of
    available hooks) can be found here: :ref:`hooks-how-to`

How to access elements
----------------------

Sometimes you may want to have access to an element after appending
it to a page. Alfred offers two convenient methods for this:

1. Attribute-style dot syntax: ``page.element_name``
2. Dictionary-style square-brackt syntax: ``page["element_name"]``

In the example below we use the dot syntax to access the element's
layout attribute and change the width definitions of the left label and
the element body::

    import alfred3 as al

    page = al.Page(name="demo")
    page += al.TextEntry(leftlab="Text entry", name="el1")
    page.el1.layout.width_sm = [6, 6]

The same can be achieved through the dictionary-style lookup using
square brackets::

    import alfred3 as al

    page = al.Page(name="demo")
    page += al.TextEntry(leftlab="Text entry", name="el1")
    page["el1"].layout.width_sm = [6, 6]


How to customize a page's validation behavior
----------------------------------------------

When you write a page in class style, you can overload the
:meth:`.Page.validate` method to implement custom validation. Take a
look at the method's documentation to learn more.

.. seealso::

   Section validation can be customized aswell:
   :ref:`How to customize validation behavior`
