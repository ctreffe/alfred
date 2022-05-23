ExperimentSession Attributes and Methods
=============================================


Administrative information (ExperimentSession)
-----------------------------------------------

.. autosummary::
    ~alfred3.experiment.ExperimentSession.config
    ~alfred3.experiment.ExperimentSession.secrets
    ~alfred3.experiment.ExperimentSession.plugins
    ~alfred3.experiment.ExperimentSession.urlargs
    ~alfred3.experiment.ExperimentSession.session_timeout
    ~alfred3.experiment.ExperimentSession.session
    ~alfred3.experiment.ExperimentSession.append
    ~alfred3.experiment.ExperimentSession.progress_bar
    ~alfred3.experiment.ExperimentSession.condition


Participant data (ExperimentSession)
----------------------------------------

.. autosummary::
    ~alfred3.experiment.ExperimentSession.get_page_data
    ~alfred3.experiment.ExperimentSession.get_section_data
    ~alfred3.experiment.ExperimentSession.all_exp_data
    ~alfred3.experiment.ExperimentSession.all_unlinked_data
    ~alfred3.experiment.ExperimentSession.values
    ~alfred3.experiment.ExperimentSession.session_data
    ~alfred3.experiment.ExperimentSession.client_data
    ~alfred3.experiment.ExperimentSession.move_history

Database access (ExperimentSession)
----------------------------------------

.. autosummary::
    ~alfred3.experiment.ExperimentSession.db
    ~alfred3.experiment.ExperimentSession.db_main
    ~alfred3.experiment.ExperimentSession.db_unlinked
    ~alfred3.experiment.ExperimentSession.db_misc

General utility (ExperimentSession)
----------------------------------------

.. autosummary::
    ~alfred3.experiment.ExperimentSession.post_message
    ~alfred3.experiment.ExperimentSession.read_csv_todict
    ~alfred3.experiment.ExperimentSession.read_csv_tolist
    ~alfred3.experiment.ExperimentSession.path
    ~alfred3.experiment.ExperimentSession.subpath
    ~alfred3.experiment.ExperimentSession.log
    ~alfred3.experiment.ExperimentSession.encrypt
    ~alfred3.experiment.ExperimentSession.decrypt
    ~alfred3.experiment.ExperimentSession.adata
    ~alfred3.experiment.ExperimentSession.additional_data

Sections and pages (ExperimentSession)
----------------------------------------

.. autosummary::
    ~alfred3.experiment.ExperimentSession.all_members
    ~alfred3.experiment.ExperimentSession.all_pages
    ~alfred3.experiment.ExperimentSession.all_sections
    ~alfred3.experiment.ExperimentSession.current_page
    ~alfred3.experiment.ExperimentSession.final_page
    ~alfred3.experiment.ExperimentSession.root_section

Movement and events (ExperimentSession)
----------------------------------------

.. autosummary::
    ~alfred3.experiment.ExperimentSession.abort
    ~alfred3.experiment.ExperimentSession.abort_functions
    ~alfred3.experiment.ExperimentSession.aborted
    ~alfred3.experiment.ExperimentSession.finish_functions
    ~alfred3.experiment.ExperimentSession.finished
    ~alfred3.experiment.ExperimentSession.session_expired
    ~alfred3.experiment.ExperimentSession.forward
    ~alfred3.experiment.ExperimentSession.backward
    ~alfred3.experiment.ExperimentSession.jump

Information about the experiment (ExperimentSession)
-------------------------------------------------------

.. autosummary::
    ~alfred3.experiment.ExperimentSession.alfred_version
    ~alfred3.experiment.ExperimentSession.author
    ~alfred3.experiment.ExperimentSession.version
    ~alfred3.experiment.ExperimentSession.metadata
    ~alfred3.experiment.ExperimentSession.session_id
    ~alfred3.experiment.ExperimentSession.session_status
    ~alfred3.experiment.ExperimentSession.start_time
    ~alfred3.experiment.ExperimentSession.start_timestamp
    ~alfred3.experiment.ExperimentSession.title
