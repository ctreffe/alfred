.. _hooks-how-to:

How to use hooks
==================

.. rubric:: What are hooks for?

Hooks are special functions ("methods", because they always belong to
classes in alfred3), that will be executed by alfred3 at fixed moments
in the experiment. Their purpose is to be redefined by you, when you
write an experiment – and that can be really powerful. Here are a few
things that you can accomplish through hooks:

- Use data from previous pages in the creation of following pages
- Use data from previous experiment sessions in the creation of
  following pages
- Jump to a certain page upon page submission, depending on the input
  given by participants.
- Add many pages with a few lines of code to a section.

.. rubric:: How do hooks work?

Most hooks (with very few exceptions) can be recognized by the fact that
they strat with *on_*. We aim to name the hooks in a way that will tell
you, at which moment in the experiment they will be executed. That's
usually the second part of the hook.

You can use a hook by defining a page or section in class style (see
:ref:`page-class-style`) and redefining the hook methods that can help
you.

.. rubric:: Example – A dynamic page

Let's say, we wish to do a calculation with a number that a
participant entered on the first page of our experiment, and show the
result to her on the following page. If we use the *instance style*, we
can't do it - because pages that are created in instance style get
filled right at the start of an experiment. At that time, our participant
has obviously not yet filled in her number.

We also can't use the *on_exp_access* hook - because that one only makes
shure that we can access the experiment session object from our page.
So, instead we utilize the *on_first_show* hook, which will only get
executed when a page is shown for the first time. A minimal experiment
would look like this::

   import alfred3 as al
   exp = al.Experiment()

   exp += al.Page(name="page1")
   exp.page1 += al.NumberEntry(toplab="Enter a number", name="n1")


   @exp.member
   class Page2(al.Page):

      def on_first_show(self):
         entered_number = self.exp.values.get("n1")
         calculated_number = entered_number - 10
         self += al.Text(f"The result of our calculation is: {calculated_number}")


In the sections below, you find a list of all available hooks - their
documentation will contain further examples.

Page Hooks
----------

.. note:: You can define multiple hook methods on the same page. In this
   case you should be aware, that elements are added to the page in order.
   To change the order of the elements on your page, you can work with
   the :attr:`.Page.elements` dictionary.


.. autosummary::
   :nosignatures:

   ~alfred3.page.Page.on_exp_access
   ~alfred3.page.Page.on_first_show
   ~alfred3.page.Page.on_each_show
   ~alfred3.page.Page.custom_move
   ~alfred3.page.Page.on_first_hide
   ~alfred3.page.Page.on_each_hide
   ~alfred3.page.Page.on_close

You can also use a hook to define custom page-specific validation:

.. autosummary::
   :nosignatures:

   ~alfred3.page.Page.validate

There is also an additional hook that is defined by
:class:`.alfred3.page.TimeoutPage`:

.. autosummary::
   :nosignatures:

   ~alfred3.page.TimeoutPage.on_timeout

Section Hooks
-------------

.. warning:: We are currently questioning the four section hooks *on_enter*,
   *on_hand_over*, *on_resume*, and *on_leave*. Everything that you may wish
   to accomplish with these hooks can be done in page hooks. The section
   versions have some caveats that make them a bit tougher
   to use correctly. So, for the meantime, please avoid these hooks and
   use page hooks instead. The attributes :attr:`.Section.first_page`
   and :attr:`.Section.last_page` may be useful for you in this regard.

   The :meth:`.Section.on_exp_access` hook is not going anywhere, although we may
   at some point decide to introduce an alternative name for it in order
   to avoid confusion with :meth:`.Page.on_exp_access`.

.. autosummary::
   :nosignatures:

   ~alfred3.section.Section.on_exp_access
   ~alfred3.section.Section.on_enter
   ~alfred3.section.Section.on_hand_over
   ~alfred3.section.Section.on_resume
   ~alfred3.section.Section.on_leave

A section's validation methods can also be used like hooks. Refer to
:ref:`How to customize validation behavior` and the docs for these
methods for more information.

.. autosummary::
   :nosignatures:

    ~alfred3.section.Section.validate_on_move
    ~alfred3.section.Section.validate_on_forward
    ~alfred3.section.Section.validate_on_backward
    ~alfred3.section.Section.validate_on_jump
    ~alfred3.section.Section.validate_on_leave


Experiment Hooks
----------------

Experiment hooks work in a different way than page and section hooks:
They require the use of decorators. Click on the names of the hooks
in the table below to get to their documentation, including examples.

.. autosummary::
   :nosignatures:

   ~alfred3.experiment.Experiment.setup
   ~alfred3.experiment.Experiment.finish
