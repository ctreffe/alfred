How to use sections
===================

Sections in alfred3 are containers that can be filled with pages and
more sections. Their main purpose is to control the ways in which
participants can move between pages in your experiment.

There are a few important things to know about sections:

1. Sections can be nested arbitrarily, which means a section can contain
   a section, which in turn contains another section, and so on ...
2. Movement is *always* controlled *only* by the section that directly
   holds the current page.
3. Sections can be written in a very similar way to pages
   (see :doc:`howto_pages`), i.e. in instance style or in class style.
4. Sections, much like pages, offer hooks. An overview can be found in
   the tutorial on hooks: :doc:`howto_hooks`
5. Sections control page and element validation, and this behavior can
   be customized easily.


How to write a section in instance style
----------------------------------------

In instance style, you add a section directly to the experiment (or the
desired parent section) using the augmented assignment operator ``+=``.
You define its name and other arguments in the instantiation call. You
can then add pages to the section in both instance and class style. The
following example using instance style for both::

    import alfred3 as al
    exp = al.Experiment()

    exp += al.Section(name="main")

    exp.main += al.Page(title="Demo page", name="page1")

For most simply purposes, it is completely sufficient to use instance
style for defining sections. But if you want more control, you can
switch to class style.

.. _section-class-style:

How to write a section in class style
-------------------------------------

In class style, you derive a new section from one of the basic sections
and add it to the experiment with the :meth:`.Experiment.member`
decorator. There are three common reasons to use class style for defining
a section:

1. You want to use one of the section hooks.
2. You want to add a lot of similar pages through a loop (this is
   actually just a very important variant of point 1).
3. You want to customize the movement behavior of pages in your section
   in a way not offered by the standard section classes.

We'll see an example for 3) below. For an example of 2), visit
the documentation on how to use loops.


..rubric:: How to customize a section's movement behavior

Sections have four class attributes that define their movement behavior:

.. autosummary::

    ~alfred3.section.Section.allow_forward
    ~alfred3.section.Section.allow_backward
    ~alfred3.section.Section.allow_jumpfrom
    ~alfred3.section.Section.allow_jumpto

When you define a section in class style, you can simply overwrite these
attributes to your liking. For example, we can define a section that
allows paticipants to move backward normally, and to jump from pages
in this section and *to* pages in this section, but not to move forward
normally.

In the example below, we define just such a section. Additionally, we
use the :meth:`.Section.on_exp_access` hook to add three pages with
jumplist elements to the section::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class MySection(al.Section):
        allow_forward = False
        allow_backward = True
        allow_jumpfrom = True
        allow_jumpto = True

        def on_exp_access(self):
            self += al.Page(name="page1")
            self += al.Page(name="page2")
            self += al.Page(name="page3")

            for page in self.pages.values():
                page += al.JumpList()


How to access pages and subsections
-----------------------------------

Sometimes you may want to have access to a page or subsection after
adding it to a section. Alfred offers two convenient methods for this:

1. Attribute-style dot syntax: ``section.page_name``
2. Dictionary-style square-brackt syntax: ``section["page_name"]``

In the example below, we use the dot syntax for a page definition in
the on_exp_access hook::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class Demo(al.Section):

        def on_exp_access(self):
            self += al.Page(name="page1")
            self.page1 += al.Text("Example text")

And here is the same example using square bracket syntax::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class Demo(al.Section):

        def on_exp_access(self):
            self += al.Page(name="page1")
            self["page1"] += al.Text("Example text")


How to customize validation behavior
------------------------------------

When you write a section in class style, you can overload the following
validation methods:

.. autosummary::
    :nosignatures:

    ~alfred3.section.Section.validate_on_move
    ~alfred3.section.Section.validate_on_forward
    ~alfred3.section.Section.validate_on_backward
    ~alfred3.section.Section.validate_on_jump
    ~alfred3.section.Section.validate_on_leave

Usage can be illustrated by looking at how *validate_on_move* is implemented::

    def validate_on_move(self):

        if not self.exp.current_page._validate_elements():
            raise ValidationError()

        if not self.exp.current_page._validate():
            raise ValidationError()

By default, *validate_on_foward* and *validate_on_backward* of a standard
:class:`.Section` simply call *validate_on_move*. You can customize them
to achieve more control over validation behavior.

Basically, whenever validation fails, any of these methods raise a
:class:`.alfred3.exceptions.ValidationError`. A very simply use case
would be to just remove validation on normal moves::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class ValidateOnLeaveOnly(al.Section):

        def validate_on_move(self):
            pass


.. seealso::

   Page validation can be customized aswell:
   :ref:`How to customize a page's validation behavior`
