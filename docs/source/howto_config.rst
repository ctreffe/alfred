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

   [metadata]
   title = My title
   author = my@email.adress
   version = 1
   exp_id = my_exp_id

Keep the section header together with the settings you copy. For example,
``title`` belongs below ``[metadata]``; it is not a standalone setting. This
also applies when editing *config.conf* in Mortimer. For settings you omit,
Alfred uses the values from its defaults or other configuration files; see
:doc:`adv_config`.

Below, you find exhaustive commented versions of the default config.conf
and secrets.conf files. They show and explain all available options.

See Also:
   More advanced configuration documentation can be found here:
   :doc:`adv_config`. This includes

   - Defining your own config options
   - Defining default configuration across multiple experiments

Colors and comments
-------------------

For example, set the header and background colors in *config.conf* like this::

   [layout]
   header_color =#ff9900
   background_color =#ddeeff

Keep the ``#`` directly after ``=`` for a hexadecimal color. A ``#`` preceded
by whitespace starts an inline comment: ``header_color = #ff9900`` is read as
an empty value. Do not put quotation marks around the color; they remain part
of the value rather than escaping the ``#``.

CSS color names and RGB expressions also work, for example
``header_color = orange`` or ``header_color = rgb(255, 153, 0)``.

config.conf
-----------

.. include:: ../alfred.conf
   :code: ini

secrets.conf
------------

.. include:: ../secrets.conf
   :code: ini
