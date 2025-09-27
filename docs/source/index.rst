.. alfred3 documentation master file, created by
   sphinx-quickstart on Wed Nov 25 09:30:13 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: README.rst

.. toctree::
   :maxdepth: 2
   :hidden:

   CHANGELOG
   plugins

.. toctree
   :maxdepth: 2
   :caption: Getting Started
   :hidden:
   installation
   first_experiment

Documentation content
----------------------

.. toctree::
   :maxdepth: 2
   :caption: How To

   howto_attributes_and_methods
   howto_exp
   howto_config
   howto_pages
   howto_sections
   howto_loops
   howto_hooks
   howto_admin

..
   howto_elements_derivation

API Reference Overview
-----------------------

This is an overview of the modules, for which documentation is available.

.. autosummary::
   :toctree: generated
   :caption: API Reference
   :recursive:
   :nosignatures:

   ~alfred3.experiment
   ~alfred3.randomizer
   ~alfred3.quota.SessionQuota
   ~alfred3.section
   ~alfred3.page
   ~alfred3.element
   ~alfred3.cli
   ~alfred3.util
   ~alfred3.admin


.. toctree::
   :maxdepth: 1
   :caption: Developers
   :hidden:

   dev_docs
   dev_plugin_data


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
