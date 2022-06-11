Section Attributes and Methods
=================================

Experiment, position, and identification (Section)
-----------------------------------------------------

.. autosummary::
    ~alfred3.section.Section.exp
    ~alfred3.section.Section.experiment
    ~alfred3.section.Section.parent
    ~alfred3.section.Section.parent_name
    ~alfred3.section.Section.section
    ~alfred3.section.Section.tree
    ~alfred3.section.Section.short_tree
    ~alfred3.section.Section.uptree
    ~alfred3.section.Section.name
    ~alfred3.section.Section.tag
    ~alfred3.section.Section.uid

Hooks for overloading (Section)
-----------------------------------------------------

.. autosummary::
    ~alfred3.section.Section.on_enter
    ~alfred3.section.Section.on_exp_access
    ~alfred3.section.Section.on_hand_over
    ~alfred3.section.Section.on_leave
    ~alfred3.section.Section.on_resume

Movement permissions (Section)
-----------------------------------------------------

.. autosummary::
    ~alfred3.section.Section.allow_backward
    ~alfred3.section.Section.allow_forward
    ~alfred3.section.Section.allow_jumpfrom
    ~alfred3.section.Section.allow_jumpto

Data and general utilities (Section)
-----------------------------------------------------

.. autosummary::
    ~alfred3.section.Section.data
    ~alfred3.section.Section.unlinked_data
    ~alfred3.section.Section.vargs
    ~alfred3.section.Section.should_be_shown
    ~alfred3.section.Section.showif
    ~alfred3.section.Section.shuffle
    ~alfred3.section.Section.subtitle
    ~alfred3.section.Section.title

Access to members and elements (Section)
-----------------------------------------------------

.. autosummary::
    ~alfred3.section.Section.all_closed_pages
    ~alfred3.section.Section.all_elements
    ~alfred3.section.Section.all_input_elements
    ~alfred3.section.Section.all_members
    ~alfred3.section.Section.all_pages
    ~alfred3.section.Section.all_shown_input_elements
    ~alfred3.section.Section.all_shown_pages
    ~alfred3.section.Section.all_subsections
    ~alfred3.section.Section.all_updated_elements
    ~alfred3.section.Section.all_updated_members
    ~alfred3.section.Section.all_updated_pages
    ~alfred3.section.Section.first_member
    ~alfred3.section.Section.last_member
    ~alfred3.section.Section.pages
    ~alfred3.section.Section.subsections

Development utilities (Section)
-----------------------------------------------------

These methods and attributes are most likely to be of interest to you
only if you derive your own sections.

.. autosummary::
    ~alfred3.section.Section.added_to_experiment
    ~alfred3.section.Section.added_to_section
    ~alfred3.section.Section.visible
    ~alfred3.section.Section.append
    ~alfred3.section.Section.instance_log
