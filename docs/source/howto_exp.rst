How to write an experiment
==========================

This guide will teach you how to approach the process of writing an
alfred experiment. We will not cover each topic in depth, but instead
touch on many relevant topics to point out, how they are connected and
how they can be used together to unleash alfred's power. Basically,
these are the steps:

1. Set up the experiment directory
2. Fill in the metadata in config.conf
3. Set up your experiment
4. Add content to your experiment, i.e. Section, Pages, and Elements.

Set up the experiment directory
-------------------------------

Start by creating a new directory. This is your experiment directory.

Now open a command line or terminal window and navigate to your experiment
directory (exchange *exp/directory* for the actual path in the example
below)::

    $ cd exp/directory

Now, execute the following command in the terminal::

    $ alfred3 template

Alfred will automatically create a minimal *script.py* and a commented
*config.conf* file for you. Now, try to run the experiment, to see if
everything goes smoothly::

    $ alfred3 run

You should see the experiment window popping up in your browser.
Congratulations! Your experiment directory is ready.

Fill in the metadata in config.conf
------------------------------------

At the top of your *config.conf*, you will find a section "metadata".
It looks like this::

    [metadata]
    title = default_title           # Experiment title
    author = default_author         # Experiment author
    version = 0.1                   # Experiment version
    exp_id = default_id             # Experiment id. MUST be unique when using a mongo saving agent

You should fill in the information for your experiment - it will make it
easier to identify data with specific experiments and authors, which
can be really helpful sometimes. The experiment version allows you to
identify datasets (and codebooks) from different versions of your experiment.
That is especially important, if you make any changes to the experiment
after data collection has begun.

The experiment id is not that important for local experiments - but once
you start to use a database to unlock alfred's full dynamic and interactive
powers, you should really make sure that you enter a unique experiment id
here. You can easily generate a unique id with two lines of Python
code::

    >>> from uuid import uuid4
    >>> uuid4().hex
    '2dbfd859bf724fa28c79d3568ae29aff'

.. note:: If you run alfred experiments on mortimer, there's no need to
    fill in the metadata in config.conf. Mortimer will set the data
    automatically (except for the experiment version, which you enter
    manually in mortimer).

You can find some more guidance on how to configure an alfred experiment
here: :doc:`howto_config`

Set up your experiment
----------------------

To apply setup operations to your experiment before it starts, alfred3
offers the :meth:`.Experiment.setup` decorator. You can use it, for
example, to assign an experimental condition via :class:`.ListRandomizer`::

    import alfred3 as al
    exp = al.Experiment()


    @exp.setup
    def setup(exp):
        # assigning a random condition
        randomizer = al.ListRandomizer.balanced("cond1", "cond2", n=10, exp=exp)
        exp.condition = randomizer.get_condition()


    # a demo page that displays the condition
    @exp.member
    class Demo(al.Page):
        title = "Demo Page"

        def on_exp_access(self):
            txt = f"You have been assigned to condition {self.exp.condition}"
            self += al.Text(txt)


You can also set a :attr:`~.ExperimentSession.session_timeout` for the experiment. The timeout is set in
seconds::

    import alfred3 as al
    exp = al.Experiment()


    @exp.setup
    def setup(exp):
        exp.session_timeout = 60 * 60 * 3 # setting timeout to 3 hours


    @exp.member
    class Demo(al.Page):
        title = "Demo Page"

        def on_exp_access(self):
            txt = f"The session will expire after {self.exp.session_timeout} seconds."
            self += al.Text(txt)



Add content to your experiment
------------------------------

You add content to the experiment in your *script.py*. The minimal
script.py will look like this::

    import alfred3 as al
    exp = al.Experiment()
    exp += al.Page(name="page1")

    if __name__ == "__main__":
        exp.run()

.. note:: To understand, what the ``if __name__ == "__main__"`` block
    in the template *script.py* created by the terminal command is for,
    you may want to watch Corey Schafer's
    explanation on YouTube: https://www.youtube.com/watch?v=sugvnHA7ElY

In script.py, you can add Sections and Pages to your experiment.

**Sections** control the navigation through the experiment. For example, you
can create an experiment in which participants can move only forward
by adding an :class:`.ForwardOnlySection`.

**Pages** generally hold Elements. But they can even do more than that -
for example, you can define a minmal amount of time that participants
have to spend on a page, before they are allowed to move forward.

**Elements** are the basic building blocks of an experiment. They can
be simply display like :class:`.Text` or :class:`.Image`, inputs like
:class:`.TextEntry`, invisible utility elements like :class:`.Style`,
or even sophisticated elements that trigger some kind of action, like
:class:`.SubmittingButtons`.

Let's bring these three concepts together to showcase a simple two-page
experiment with a text entry field on each page. Participants will only
be able to move forward in this experiment::

    import alfred3 as al
    exp = al.Experiment()

    exp += al.ForwardOnlySection(name="main")

    exp.main += al.Page(name="page1")
    exp.main.page1 += al.TextEntry(leftlab="Enter here", name="t1")

    exp.main += al.Page(name="page2")
    exp.main.page2 += al.TextEntry(leftlab="Enter here", name="t2")


So now you know about sections, pages, and elements. You can find
overviews of the available classes in the respective API reference pages:

.. autosummary::

    ~alfred3.section
    ~alfred3.page
    ~alfred3.element

Implement dynamic content
-------------------------

In alfred, you can dynamically access data in three ways:

1. Inside an experiment, you can access data entered on previous pages.
2. You can access data from other sessions of the same experiment.
3. You can access data from other experiments.

To utilize 2) and 3) to their full extent, alfred needs to work with a database, which can be
done either by using a *mongo_saving_agent* (see :doc:`howto_config`), or
by running your experiment on Mortimer (https://github.com/ctreffe/mortimer).
For 3), you also need to know the experiment ID of the experiment from
which you want to query data, which means you have to either be their
author or ask the author.

The interfaces for dynamic content are, in large parts, provided by
the :class:`.ExperimentSession` object. You will need access to this
object when writing sections and pages (or when you derive new elements).
For this purpose, we provide a number of hooks, which can be utilized in
the "class style" of writing sections and pages. Our documentation
contains guides on :doc:`howto_hooks`, :ref:`page-class-style`, and
:ref:`section-class-style`.

Here is an example for a two-page experiment, in which the second page
uses data from the first page by simply displaying it::

    import alfred3 as al
    exp = al.Experiment()

    exp += al.Page(name="page1")
    exp.page1 += al.TextEntry(leftlab="Enter something", name="t1")

    @exp.member
    class Page2(al.Page):

        def on_first_show(self):
            input_on_page1 = self.exp.values["t1"]
            self += al.Text(input_on_page1)


Add content with loops
----------------------

Loops are so powerful, it's almost ridiculous. You can add virtually
unlimited amounts of similar section, pages, and elements with minimal
code by using loops. If you would like to find out about this feature,
check out :doc:`howto_loops`.
