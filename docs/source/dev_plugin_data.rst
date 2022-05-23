Plugin data interface
======================

Alfred3 offers an interface for database-using plugins to make their data
accessible for export. For example, the ``alfred3_interact`` plugin offers
the ``alfred3_interact.element.Chat`` element. Through the plugin data
interface, experimenters can export, for instance, the messages exchanged
by participants during the chat via our administration tool Mortimer.

How to use the plugin data interface
-------------------------------------

Follow the instructions below to

1. Create a suitable query dictionary
2. Append the query dictionary to the ExperimentSession object.

.. automethod:: alfred3.experiment.ExperimentSession.append_plugin_data_query
    :noindex:


Example
--------

The example shows only the relevant parts of the ChatManager class that
administrates the chat data under the hood for the Chat element. The
chat data is saved to :attr:`.ExperimentSession.db_misc`, and the
specified filter will allow Mortimer or the experimenter to retrieve
the chat data from the database.::

    class ChatManager:

        def __init__(self, exp):
            self.exp = exp
            self.exp.append_plugin_data_query(self._plugin_data_query)

            ...

        @property
        def _plugin_data_query(self):
            f = {"exp_id": self.exp.exp_id, "type": "chat_data"} # filter for database search

            q = {}
            q["title"] = "Chat" # human-readable title, for example for display in Mortimer
            q["type"] = "chat_data"
            q["query"] = {"filter": f}

            # signals that at least some part of the data is saved in encrypted form. This
            # allows Mortimer or the experimenter to decrypt it for export.
            q["encrypted"] = True

            return q

        ...
