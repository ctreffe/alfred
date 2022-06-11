How to configure an experiment
==============================

.. toctree::
   :hidden:

   adv_config

Alfred comes with a lot of sensible defaults, but can be flexibly
configured by users.

Configuration relies on two files:

.. csv-table::
   :widths: 20, 80

   config.conf,   General configuration file (can be shared with others).
   secrets.conf,  Secret configuration like database credentials

You simply place either of these files in your experiment directory.
Alfred will find and read them automatically.

You need to fill only the fields that you need in your experiment,
everything else will be covered by alfred automatically. For example,
a config.conf might often look like this, with only the metadata
defined::

   [metdata]
   exp_title = My title
   author = my@email.adress
   version = 1
   exp_id = my_exp_id

Below, you find exhaustive commented versions of the default config.conf
and secrets.conf files. They show and explain all available options.

See Also:
   More advanced configuration documentation can be found here:
   :doc:`adv_config`. This includes

   - Defining your own config options
   - Defining default configuration across multiple experiments

config.conf
-----------

.. include:: ../alfred.conf
   :code: ini

secrets.conf
------------

.. include:: ../secrets.conf
   :code: ini
