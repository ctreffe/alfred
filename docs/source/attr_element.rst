Element
========

Element base class
---------------------

Experiment, position, and identification (Element)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    ~alfred3.element.core.Element.exp
    ~alfred3.element.core.Element.experiment
    ~alfred3.element.core.Element.name
    ~alfred3.element.core.Element.page
    ~alfred3.element.core.Element.section
    ~alfred3.element.core.Element.tree
    ~alfred3.element.core.Element.short_tree


General utilities (Element)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    ~alfred3.element.core.Element.converted_width
    ~alfred3.element.core.Element.element_width
    ~alfred3.element.core.Element.width
    ~alfred3.element.core.Element.position
    ~alfred3.element.core.Element.font_size
    ~alfred3.element.core.Element.css_class_container
    ~alfred3.element.core.Element.css_class_element
    ~alfred3.element.core.Element.should_be_shown
    ~alfred3.element.core.Element.showif


Development utilities (Element)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These methods and attributes are most likely to be of interest to you
only if you derive your own sections.

.. autosummary::
    ~alfred3.element.core.Element.add_css
    ~alfred3.element.core.Element.css_code
    ~alfred3.element.core.Element.css_urls
    ~alfred3.element.core.Element.add_js
    ~alfred3.element.core.Element.js_code
    ~alfred3.element.core.Element.js_urls
    ~alfred3.element.core.Element.added_to_experiment
    ~alfred3.element.core.Element.added_to_page
    ~alfred3.element.core.Element.prepare_web_widget
    ~alfred3.element.core.Element.render_inner_html
    ~alfred3.element.core.Element.base_template
    ~alfred3.element.core.Element.element_template
    ~alfred3.element.core.Element.template_data
    ~alfred3.element.core.Element.web_widget

LabelledElement Attributes and Methods (Element)
--------------------------------------------------

.. autosummary::
    ~alfred3.element.core.LabelledElement.rightlab
    ~alfred3.element.core.LabelledElement.leftlab
    ~alfred3.element.core.LabelledElement.toplab
    ~alfred3.element.core.LabelledElement.bottomlab
    ~alfred3.element.core.LabelledElement.labels

InputElement Attributes and Methods (Element)
-----------------------------------------------


Data (InputElement)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    ~alfred3.element.core.InputElement.data
    ~alfred3.element.core.InputElement.codebook_data
    ~alfred3.element.core.InputElement.input


General utilities (InputElement)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    ~alfred3.element.core.InputElement.hint_manager
    ~alfred3.element.core.InputElement.corrective_hints
    ~alfred3.element.core.InputElement.show_hints
    ~alfred3.element.core.InputElement.default_no_input_hint
    ~alfred3.element.core.InputElement.prefix
    ~alfred3.element.core.InputElement.suffix
    ~alfred3.element.core.InputElement.debug_enabled
    ~alfred3.element.core.InputElement.debug_value
    ~alfred3.element.core.InputElement.default
    ~alfred3.element.core.InputElement.disabled
    ~alfred3.element.core.InputElement.force_input
    ~alfred3.element.core.InputElement.description


Development utilities (InputElement)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These methods and attributes are most likely to be of interest to you
only if you derive your own sections.

.. autosummary::
    ~alfred3.element.core.InputElement.set_data
    ~alfred3.element.core.InputElement.validate_data
