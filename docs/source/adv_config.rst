Advanced configuration
==================================

This tutorial teaches you how to

- Definine your own config options
- Definine default configuration across multiple experiments

Define your own config options
------------------------------

Defining your own config options is as easy as adding them to your
config.conf. Let's illustrate this with an example. Here, we first
define a new section "custom" in config.conf, and add an option of name
"my_option", which we equip with a value::

    # config.conf
    [custom]
    my_option = Value defined in config.conf

Now, in our script.py we can access the values defined in config.conf
(and the default values provided by alfred) anywhere where we have
access to the :class:`.ExperimentSession` object. That's usually the
case in hooks. Here, we just display the value defined in config.conf::

    # script.py
    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class Demo(al.Page):

        def on_exp_access(self):

            text = self.exp.config.get("custom", "my_option")
            self += al.Text(text)


.. note::
   **Notes**

   - Keep in mind that *script.py* and *config.conf* need to reside in the
     same directory (the experiment directory).
   - The behavior documented here works exactly the same for *secrets.conf*
   - Since we use a :class:`configparser.ConfigParser` as the base for
     alfred's config handling, you need to know that you have to
     explicitly define the type of object that you want to retrieve when
     accessing a config option. *ConfigParser* provides four distinct
     methods for this purpose:

   .. csv-table::

      :meth:`.ConfigParser.get`, returns a string
      :meth:`.ConfigParser.getint`, returns an integer
      :meth:`.ConfigParser.getfloat`, returns a floating point number
      :meth:`.ConfigParser.getboolean`, returns a boolean value

.. warning::
   It is recommended, that you place your custom options only a new
   section dedicated entirely for custom options, like in the example
   above. Otherwise you are at a risk of unknowingly overriding default
   options defined by alfred.

See Also:
    - Documentation on hooks: :doc:`howto_hooks`
    - API documentation of alfred's config classes: :mod:`.alfred3.config`

Define default configuration
----------------------------

User-defined configuration files that can affect multiple experiments are
parsed in the following order (later files override settings from earlier ones):

1. "alfred.conf" ("secrets.conf" for secrets) in "/etc/alfred/"
   (for unix operating systems)
2. "alfred.conf" ("secrets.conf") in the user's home directory
3. File found under path given in the environment variable
   "ALFRED_CONFIG_FILE" ("ALFRED_SECRETS_FILE")

.. note::
   A *config.conf* (*secrets.conf*) in the experiment directory will
   always be parsed last and override any default configuration.
