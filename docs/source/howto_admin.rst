How to use the admin mode
================================

Your alfred3 experiments are not limited to the pages that participants
see. You can add an administrative layer of pages that make organizational
tasks around the experiment easier. This how-to covers 1) how to activate
the admin mode, 2) how to add admin pages to an existing experiment,
3) how to access the admin mode, 4) how to distinguish the access levels
of the admin mode, and 5) how to write your own admin pages.


How to activate the admin mode
-------------------------------

You activate the admin mode by defining three different passwords in
your ``secrets.conf``::

    # secrets.conf
    [general]
    adminpass_lvl1 = demo
    adminpass_lvl2 = use-better-passwords
    adminpass_lvl3 = to-protect-access

As you can see, we have three access levels. For now, we only note that
you *have to* define passwords for all levels to activate the admin mode,
otherwise the experiment will crash if you try to open the admin view.

.. note:: The characters ``|`` and ``#`` cannot be used in admin passwords.

We'll explain the meaning of the three levels later.

How to add admin pages
-----------------------

Once you have activated the admin view, you can add pages to your admin
mode. This works in a way that is very similar to ordinary experiment
creation with a slight modification. The :class:`.Experiment` object
has a special attribute :attr:`.Experiment.admin`. Instead of adding
a page directly to the experiment or using the :meth:`.Experiment.member`
decorator, you add admin pages to the *admin* attribute with the well-known
``+=`` operator.

For a little demonstration, we will add an empty admin page to a minimal
experiment. We start with the "hello world" setup::

    import alfred3 as al
    exp = al.Experiment()
    exp += al.Page("Hello, world!", name="hello_world")

To have access to a basic admin page, we now import the base class
:class:`.SpectatorPage`. This step is not always strictly necessary,
because you may possibly get your admin page from elsewhere::

    import alfred3 as al
    from alfred3.admin import SpectatorPage

    exp = al.Experiment()
    exp += al.Page("Hello, world!", name="hello_world")

Next, we add the page to the experiment's admin attribute::

    import alfred3 as al
    from alfred3.admin import SpectatorPage

    exp = al.Experiment()
    exp.admin += SpectatorPage(title="My monitoring page", name="monitoring")

    exp += al.Page("Hello, world!", name="hello_world")


Add pages by decorating classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also use the :meth:`.Experiment.member` decorator to add pages
to your admin mode. This works just like adding ordinary pages through
the decorator, you just need to add ``admin=True``::

    import alfred3 as al
    from alfred3.admin import SpectatorPage

    exp = al.Experiment()

    @exp.member(admin=True)
    class MyAdminPage(SpectatorPage):
        title = "Spectator"

        def on_exp_access(self):
            self += al.Text("My admin page")


    exp += al.Page("Hello, world!", name="hello_world")


How to access the admin mode
-------------------------------

You can access the admin mode by adding ``?admin=true`` to the experiment's
start link. If you are running a local experiment, this means that you
can use::

    http://127.0.0.1:5000/start?admin=true

Note that the question mark only signals the beginning of additional
url arguments. If you use multiple url arguments, they are chained via
``&``. For example, the following url would *also* start the experiment
in admin mode::

    http://127.0.0.1:5000/start?demo=this&admin=true

When you open the link to the admin mode, you face a page asking you
for a password. If you encounter an "Internal Server Error", you should
check the log - you may have forgotten to specify all necessary passwords.

If you enter a correct password, you can move on to the admin pages. Based
on your password, you may see only a subset of all possibly available pages.
With the level 1 password, you can only see level 1 pages. With the level 2
password, you can see level 1 and level 2 pages. And with the level 3
password, you have full access to pages of all three levels.


How to distinguish the access levels
-------------------------------------

When you collaborate with others on an experiment, you may want to share
access to certain admin functionality, but at the same time not hand over
full control. The three access levels are intended to give you some
flexibility in this regard.

The levels are defined by :class:`.AdminAccess`. They are:

- Level 1: Lowest clearance. This level should be granted to
  pages that display additional information but do not allow active
  intervention. Used by :class:`.SpectatorPage`.
- Level 2: Medium clearance. This level should be granted to
  pages that allow non-critical actions like exporting data or sending
  emails.
- Level 3: Highest clearance. This level should be granted to
  pages that allow the most critical actions, e.g. permanent data
  deletion. As a rule of thumb, only one person should have level 3
  access for an experiment.

By the way: you can specficy multiple passwords for the same level to enable
a token-like authentication management. To specifiy multiple passwords,
simply separate them by ``|``::

    # secrets.conf
    [general]
    adminpass_lvl1 = demo|demopass-2
    adminpass_lvl2 = use-better-passwords
    adminpass_lvl3 = to-protect-access

How to write your own admin pages
-----------------------------------

To write your own admin pages, you can inherit from three base classes
that are provided by alfred3. The classes correspond to the three access
levels. They are:

- :class:`.admin.SpectatorPage` for level 1 access
- :class:`.admin.OperatorPage` for level 2 access
- :class:`.admin.ManagerPage` for level 3 access

To build your admin page, you first import your desired base class::

    from alfred3.admin import SpectatorPage

Next, you define a new page class just as you would define an ordinary
page in an experiment. Here, we simply display the number of datasets
associated with the experiment::

    from alfred3.admin import SpectatorPage

    class MyAdminPage(SpectatorPage):
        def on_exp_access(self):
            n = len(self.exp.all_exp_data)
            self += al.Text(f"Number of data sets: {n}")

You have access to alfred3's full functionality in admin mode. Useful
attributes may be the ones that grant access to experiment data through
:attr:`.ExperimentSession.all_exp_data`, or the :class:`.Button` element
for triggering the execution of Python code on the click of a button. But
always take care!



One last thing:
