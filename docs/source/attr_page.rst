Page Attributes and Methods
=============================

Experiment, position, and identification (Page)
------------------------------------------------

.. autosummary::
    ~alfred3.page.Page.exp
    ~alfred3.page.Page.experiment
    ~alfred3.page.Page.section
    ~alfred3.page.Page.parent
    ~alfred3.page.Page.parent_name
    ~alfred3.page.Page.tree
    ~alfred3.page.Page.uptree
    ~alfred3.page.Page.short_tree
    ~alfred3.page.Page.name
    ~alfred3.page.Page.tag
    ~alfred3.page.Page.uid

Hooks for overloading (Page)
----------------------------------------------

.. autosummary::
    ~alfred3.page.Page.custom_move
    ~alfred3.page.Page.on_close
    ~alfred3.page.Page.on_each_hide
    ~alfred3.page.Page.on_each_show
    ~alfred3.page.Page.on_exp_access
    ~alfred3.page.Page.on_first_hide
    ~alfred3.page.Page.on_first_show

Data and general utilities (Page)
----------------------------------------------

.. autosummary::
    ~alfred3.page.Page.data
    ~alfred3.page.Page.unlinked_data
    ~alfred3.page.Page.durations
    ~alfred3.page.Page.first_duration
    ~alfred3.page.Page.last_duration
    ~alfred3.page.Page.has_been_shown
    ~alfred3.page.Page.must_be_shown
    ~alfred3.page.Page.should_be_shown
    ~alfred3.page.Page.is_closed
    ~alfred3.page.Page.minimum_display_time
    ~alfred3.page.Page.title
    ~alfred3.page.Page.subtitle
    ~alfred3.page.Page.showif
    ~alfred3.page.Page.vargs

Access to elements (Page)
----------------------------------------------

.. autosummary::
    ~alfred3.page.Page.all_elements
    ~alfred3.page.Page.all_input_elements
    ~alfred3.page.Page.filled_input_elements
    ~alfred3.page.Page.updated_elements

Visual settings (Page)
----------------------------------------------

.. autosummary::
    ~alfred3.page.Page.background_color
    ~alfred3.page.Page.fixed_width
    ~alfred3.page.Page.responsive_width

Development utilities (Page)
----------------------------------------------

These methods and attributes are most likely to be of interest to you
only if you derive your own pages.

.. autosummary::
    ~alfred3.page.Page.added_to_experiment
    ~alfred3.page.Page.added_to_section
    ~alfred3.page.Page.append
    ~alfred3.page.Page.prepare_web_widget
    ~alfred3.page.Page.save_data
    ~alfred3.page.Page.visible
    ~alfred3.page.Page.instance_log
