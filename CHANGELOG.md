# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/).
<!-- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

<!--
Guiding Principles

Changelogs are for humans, not machines.
There should be an entry for every single version.
The same types of changes should be grouped.
Versions and sections should be linkable.
The latest version comes first.
The release date of each version is displayed.
Mention whether you follow Semantic Versioning.

Types of changes

1. Added for new features.
2. Changed for changes in existing functionality.
3. Deprecated for soon-to-be removed features.
4. Removed for now removed features.
5. Fixed for any bug fixes.
6. Security in case of vulnerabilities.
-->

## Newer versions

See https://github.com/ctreffe/alfred/releases

## alfred3 v2.4.0 (Released 2023-03-31)

### Added v2.4.0

- #220
- #221

### Changed v2.4.0

- #203

### Fixed v2.4.0

- #222
- #223


## alfred3 v2.3.4 (Released 2023-03-31)


### Fixed v2.3.4

- Correctly export `DateEntry` and `TimeEntry` elements for date and time input
- Removed dependency on mongomock for standard usage. It is still required for
  development, since it is used in the unit tests.

## alfred3 v2.3.3 (Released 2022-06-18)

### Changed v2.3.3

- Improved efficiency of the ListRandomizer

### Fixed v2.3.3

- Fixed buggy recognition of expired sessions in the ListRandomizer

## alfred3 v2.3.2 (Released 2022-05-05)

### Added v2.3.2

- Added `DateEntry` and `TimeEntry` elements for date and time input.
- Added `DeleteUnlinkedPage`. This page allows you to delete the unlinked
  data associated to a specific experiment. Must be imported from
  `alfred3.admin` directly.
- Added `ExperimentSession.tmp`, which is a dictionary for temporary data
  that does not need to be saved to the experiment data.
- Added parameter `silent` to `Element.validate_data` (#191)

### Changed v2.3.2

- `alfred3.Card` elements with *collapse=True* will now start in collapsed
  view.
- Any call to `Experiment.finish()` will only go through now, if the experiment
  session is *not* already aborted.
- Some small updates to the documentation, most notably regarding the command
  line interface (CLI).

### Fixed v2.3.2

- Hotfix for #174
- Fixed #141
- Fixed #144
- Fixed #139
- Fixed #169
- Fixed #157
- Fixed #185
- Closed #187, #184, #196, #172, #178, #195
- Fixed an issue that lead `alfred3.Card` elements to render sub-elements
  as codeblocks instead of correctly displaying their full web widget.
- Fixed an issue that lead `alfred3.Card` elements to not add input elements
  to the parent page in the intended way.
- Fixed an issue in `ExperimentSession.all_unlinked_data` for access to
  *local* unlinked data.


## alfred3 v2.3.1 (Released 2021-10-28)

### Fixed v2.3.1

- Fixed an issue with string inputs to `NumberEntryElement` that was
  introduced in v2.3.0

## alfred3 v2.3.0 (Released 2021-10-28)

### Added v2.3.0


- New Elements
  - Added `RangeInput` element, a slider for number entry.
  - Added `SubmittingBar`, the sibling of the already existing `SubmittingButtons`
  - Added `MatchEntry` as alias for `RegEntry` element
  - Added `EmailEntry` element. This is a `MatchEntry` element that offers
    a default validation for email inputs.
  - Added the elements `BackButton` and `ForwardButton`, which do as they say.
  - Added a `Card` element that can be used for displaying text and other
    elements in bootstraps nice-looking cards. The highlight of the card
    element is its possibility to turn the header into a button that hides
    or shows the card body on click via the argument *collapse*.
- Pages and Sections
  - We are excited to present the new section class `HideOnForwardSection`:
    A section that hides pages
    once they have been submitted. This is basically a slightly more liberal
    version of a `ForwardOnlySection`. Take a look at the documentation
    for more details!
  - Added the methods `Page.position_in_section` and `Section.position_in_section`.
    These are used to get the position of the current page or section inside
    its parent section, which can be useful if you create section or pages
    in loops.
- Codebook
  - The codebook now includes the number of choices for all choice elements
    (#114)
  - On codebook export, alfred3 will check if the two newest sessions contain
    identical element labels. If not, alfred3 will log a warning. This can
    help users to discover unfortunate element or page randomization setups.
- Different modes
  - Added a test mode (#90). If you start an experiment with the url parameter
    `?test=true`, the experiment starts in test mode. The test mode's only
    effect is that it prefixes session IDs of test sessions with "test-".
    Test mode is active in debug mode aswell.
      + **Keep in mind** that a test session will take up a slot in list
        randomization just as any other session. You have to use experiment
        version numbers to manage randomization slots.
  - Added the possibility to start the "debug" mode with the url parameter
    `?debug=true`. Debug mode is a "fancy test mode" - session IDs created
    in debug mode will be prefixed with "test-".
  - Added the parameter `test` to `ExperimentRunner.auto_run` and, subsequently,
    to `Experiment.run`

To start an experiment in test mode locally, you can use this parameter
in the ``if __name__ == "__main__"`` block:

```python
import alfred3 as al
exp = al.Experiment()
exp += al.Page(name="demo")

if __name__ == "__main__":
    exp.run(test=True)
```

- Miscellaneous
  - Added the prefix "sid-" to session IDs.
  - Added the possibility to download the randomizer's data in Mortimer (#112).
  - alfred3 now saves the length of the session timeout to the experiment
    data (#113)

### Changed v2.3.0

- Changed the default design. The top bar is now white instead of red.
- Sections will now immediately raise an error, if you mistakenly define
  a page-only hook like `on_first_show` or `on_first_hide` on a section,
  which can be a common but very hard-to-debug programming error.
- The `NumberEntry` element now returns its value as a `float`. Previously,
  the value was returned as a string, which was unexpected behavior in
  most cases.
- From now on, sections do not close all of their pages by default on leaving.
  Instead, you can override the attribute `close_pages_on_leave`. By setting
  it to *True*, a section will close all its pages when it is left.
- Minimal finetuning of the progress bar: It can now be set to zero progress.


### Fixed v2.3.0

- Some updates to the documentation
- Fixed the option "logo_text" in the section "layout" in `config.conf`
- Fixed the "shuffle" argument of Sections. Previously, it did not
  successfully lead to randomization of the pages and subsections in a
  section. It affects only first-level subsections, i.e. the order of
  subsections is randomized, but the order of pages inside those
  subsections is not affected.
- Fixed the defaults for SingleChoice element and its children that are
  used in debug mode (#125).

## alfred3 v2.2.2 (Released 2021-10-14)

The last update (v2.2.1) did not contain the intended changes. This update
fixes this issue.

### Changed v2.2.2

- We temporarily deactivated the `MultipleChoiceList` element, because
  we have to sort out some issues with it. It has seen no use so far, so
  the deactivation should not be a problem.


### Fixed v2.2.2

- We fixed some encoding issues on Windows machines.
- We fixed some issues in the documentation.


## alfred3 v2.2.1 (Released 2021-10-14)

### Changed v2.2.1

- We temporarily deactivated the `MultipleChoiceList` element, because
  we have to sort out some issues with it. It has seen no use so far, so
  the deactivation should not be a problem.

### Fixed v2.2.1

- We fixed some encoding issues on Windows machines.
- We fixed some issues in the documentation.

## alfred3 v2.2.0 (Released 2021-10-14)

### Added v2.2.0

- Added `alfred3.SessionQuota`, a class for smart session counting. You
  can use it to control the maximum number of participants to your
  experiment. The SessionQuota is a new parent class to ListRandomizer.

- Added a new admin mode to alfred3 that you can use to access experiment
  information and manage your experiment (#113). You can also grant access to
  others on three different levels of authorization. You can add
  functionality to your experiment's admin mode by adding pages, just like
  you add pages to an ordinary experiment. You start it by adding
  `?admin=true` to the experiment's start url.
  Please refer to the official documentation for more details.

- Added `alfred3.PasswordPage`, a wide page that can be used to restrict
  access.

- Added lots of automatic unit tests.

### Changed v2.2.0

- Removed the method *ListRandomizer.abort_if_full*. Instead, you can check
  the randomizer's status with the attributes :attr:`.full`,
  :attr:`.allfinished`, :attr:`.nopen`, :attr:`.npending`, and
  :attr:`.nfinished` and call :meth:`.ExperimentSession.abort`
  directly.

- We turned `Page.showif` and `Section.showif` into hooks that you can use
  to dynamically control whether a page or section is shown or not. You
  use it by overloading
  the method when writing a page or section in class style. If the method
  returns *True*, the page or section is shown, if it returns *False* it
  is not shown.

### Fixed v2.2.0

- Fixed #118

## alfred3 v2.1.7

### Added v2.1.7

- Added the `ListRandomizer.factors` alternative constructor for the
  ListRandomizer. This constructor allows experimenters to easily create
  a set of conditions from combinations of factors. For instance,
  factor 1 with values "A1" and "A2" can be combined with factor 2, which
  has values "B1" and "B2". The result will be four conditions:
  "A1.B1", "A1.B2", "A2.B1", "A2.B2". Take a look at the
  [documentation]() for further instructions and examples.

- Added the `ListRandomizer.abort_if_full` method. This method allows
  experimenters to conveniently abort the experiment if all condition
  slots are full, independently of condition assignment.

### Deprecated v2.1.7

- Deprecated the `id` argument of `ListRandomizer`. Please use the
  new parameter `session_ids` in the future. The new parameter is designed
  to work exclusively with **lists** of session ids, wich can be useful for
  group studies conducted with *alfred3-interact*.

## alfred3 v2.1.6 (Released 2021-06-12)

### Fixed v2.1.6

- Fixed an issue with the upper allocation limits of the
  `ListRandomizer`.

## alfred3 v2.1.5 (Released 2021-06-09)

### Added v2.1.5

- You know how Facebook, Twitter, WhatsApp, etc. all create small
  previews for websites, if you post a link? Well, if you host alfred3
  on a Mortimer v0.8.9 or newer, alfred3 now supports these previews.
  And in alfred3's `config.conf`, you can now set the following options
  in the section `[layout]`:

```ini
[layout]
# Settings for previews on social media services
preview_title = Online-Studie               # Title MAX 35 characters
preview_description = Jetzt mitmachen und Teil der aktuellen Forschung werden. # Description MAX 155 characters
preview_image =                             # Full URL to custom preview image (2063 + 1080 px) (For Facebook and similar)
preview_image_small =                       # Full URL to custom preview image for small versions (300 x 200 px) (for WhatsApp an similar)
```

### Changed v2.1.5

- Changed the default footer
- Changed the default width of `alfred3.Text` element to `with="full"`.
  Previously, we tried to be smart about the text's default width, making
  it smaller for optimizing redability. But that was not in line with how
  users expected and wished the text to behave, because it often caused
  misalignment between full-width input elements and the narrower text.

### Fixed v2.1.5

- Fixed an issue with the `DataManager`, causing client information to be
  unreliable.



## alfred3 v2.1.4 (Released 2021-06-03)

### Fixed v2.1.4

- Fixed some layout issues
- Fixed an incompatibility issue with jinja2 v3.0

## alfred3 v2.1.3 (Released 2021-06-01)

### Fixed v2.1.3

- Fixed a bug in `ListRandomizer` that impaired the allocation of excat numbers
  of participants to conditions. With this bug, random allocation to conditions
  was not affected, but the `ListRandomizer` operated like a true pseudo-random
  allocator instead of using actual list randomization: If you defined conditions
  "a" and "b" to get 20 participants each, you may have ended up with 22
  participants in condition "a" and 26 in condition "b" instead.
  This was update fixes this bug and includes 19 automatic unit tests that make
  sure that the randomizer works as intended.

### Removed v2.1.3

- Removed the parameter `timeout` from `ListRandomizer`. The randomizer will now
  always use the `ExperimentSession.session_timeout` to determine whether a
  session is expired.

## alfred3 v2.1.2 (Released 2021-05-27)

### Added v2.1.2

- New parameter *start_time* for `CountUp` element.

## alfred3 v2.1.1 (Released 2021-05-18)

### Changed v2.1.1

- We now save a basic skeleton of an experiment's data directly on
  initializing a session. While this introduces a short delay (max 1s)
  upon starting an experiment, this makes it easier for plugins such
  as `alfred3_interact` to rely on certain data being available during
  setup.

## alfred3 v2.1.0 (Released 2021-05-14)

### Added v2.1.0

- `alfred3.multiple_choice_names`: A new utility function that you can
  use to find the indexes of selected choices in multiple choice elements.
  You can apply it to the data dictionary corresponding to the element of
  interest in `alfred3.experiment.ExperimentSession.values`, or to the
  `input` attribute of the element directly.
- Four new hooks for finetuning a section's validation behavior. All
  except `validate_on_jumpto` default to calling `validate_on_move`. Their
  intended use is to allow for specialized behavior by being overloaded.
  For example, you can implement a section that does not validate input on
  backwards movements by overriding the `validate_on_backward` method with
  an empty method. These are the locations:
    - `alfred3.section.Section.validate_on_forward`
    - `alfred3.section.Section.validate_on_backward`
    - `alfred3.section.Section.validate_on_jumpfrom`
    - `alfred3.section.Section.validate_on_jumpto`
- Pages can now have a customized validation method: Simply overload
  (redefine) `alfred3.Page.validate` when writing a page in class style.
  The method must return *True* if validation was successful and *False*
  otherwise. You can and should use `alfred3.experiment.ExperimentSession.post_message`
  (available in a page instance via `self.exp.post_message`) to inform
  participants about the reason for validation failures. This custom page
  validation will be executed *after* all standard validation checks for the
  page and its elements.
- The command line interface for getting an experiment template now offers
  a `-b` option, which you can use to get a slightly more extensive template.
  This template will include a `secrets.conf`, a `.gitignore`, and a more
  extensive `script.py` next to the usual `config.conf`. Use it by calling
  `alfred3 template -b` in from a terminal session.
- Data saving can be turned off for individual elements via the argument
  `save_data`, which of course defaults to `True`.
- We added a public `ExperimentSession.finish` method. This method can be
  used to finish an experiment session earlier than usual, which may be
  useful if you want to mark a session as complete but still show some
  optional information to participants. Previously, if participants left
  the experiment during such an optional part before clicking all the way
  through to the end, the session could not be marked as finished, even
  though all data was available and correct. (#78)


### Changed v2.1.0

- **On last notice, we decided to change the input representation of single
  choice elements**:
    - SingleChoice type elements use an integer to represent participant
      input, which starts counting at 1. Previously, they used the same
      representation as MultipleChoice type elements, which lead to
      unnecessarily overcrowded output data. Now, each SingleChoice
      element will by represented by only one variable in the final dataset.
    - MultipleChoice type elements remain the same: For each choice, they
      have a dummy variable, which indicates whether that specific choice
      was selected (True/False). Within alfred3, this takes the form of
      a dictionary with an entry for each choice. In the final dataset,
      there is a dummy variable for each choice.
    - SingleChoice**List** type elements use a string to represent
      participant input. The string is the exact choice label that was
      selected. This representation reflects the fact that SingleChoiceLists
      are intended to be comfortable with really long lists of possible
      choices. In such lists, it is hard to keep track of the meaning
      of integers. Also, the SingleChoiceList does not accept any other
      form of labels than strings. That is a difference from ordinary
      SingleChoice type elements, which can accept other elements (e.g.
      ImageElements). This fact makes it unproblematic to use the string
      representation. You can still access the index of a selected choice
      label: The list of labels is saved in the element's attribute
      `choice_labels`, which has a method `index`. Supply this method
      with the selected choice string, and you get the index of that string
      in the list of choice labels. *Be aware though, that in this case,
      python will start counting at 0!*
- `alfred3.page.TimeoutPage` and its two child classes
  `alfred3.AutoForwardPage` and `alfred3.AutoClosePage` received a new,
  more robust implementation with an additional argument *callbackargs*.
  Check out the documentation for more details. Also, they now accept an
  integer as in the `timeout` argument in addition to string. The integer
  version gives the timeout in seconds.
- `alfred3.Row` now offers an additional *layout* parameter similar to
  the implementation used in `alfred3.element.core.LabelledElement`
- `alfred3.Callback` and `alfred3.RepeatedCallback` have seen some
  improvements, including additional arguments and docstrings.
- Clarified the default match hints for NumberEntry elements.
- For all input elements, their `input` attribute now clearly states the
  type of the returned input.
- Image, Audio, and Video elements now support labels like input elements
  do: You can use the arguments `leftlab`, `rightlab`, `toplab`, and
  `bottomlab`.


### Fixed v2.1.0

- Some problems with input handling in choice elements
- A small visual hickup with a verbose message displayed upon using the
  debug jump mode
- Fixed a problem in `ExperimentSession.all_exp_data` and
  `ExperimentSession.all_unlinked_data`.
- Fixed a hole in the input validation of `alfred3.NumberEntry` elements.
  If the minimum or maximum was excatly zero, user input did not get
  validated correctly.
- Fixed a problem that prevent the final page from being set correctly.
- Fixed the *path* argument of `alfred3.JavaScript`
- Fixed the *custom_js* argument of `alfred3.Button`
- Fixed some alignment issues
- JumpLists do not save any data in debug mode anymore (#79)
- Fixed suboptimal saving of suffixes and prefixes in the codebook (#77)
- Errors trough multiple accidental (or impatient) clicks on the
  navigation buttons are prevented (#75)
- SubmittingButtons now work as expected in Firefox (#76)


## alfred3 v2.0.0 (Released 2021-04-20)

We are excited to announce the release of alfred3 v2.0!

**Note**: This is a major release. While the basic building blocks of
alfred3 experiments – sections, pages, and elements – remain at the heart
of the framework's logic, many other aspects have undergone
disruptive changes. These are too many to sensibly detail all of them
here. We recommend instead to start from scratch using the new
documentation: [Link to docs](https://jobrachem.github.io/alfred_docs/html/index.html)

In short, the biggest changes are the following:

* New syntax: Experiments in alfred3 v2.0 can be written in what we call
  the instance-style or the class-style. Together they replace the previous
  style of writing an experiment. We also streamlined the
  element names, removing the suffix "Element". For instance,
  `TextEntryElement` can now be accessed under the name `TextEntry`.

* We added a number of elements that
  should make your life easier when writing dynamic, or even interactive
  experiments.

* We added a number of attributes to the `ExperimentSession` object to
  make your life a lot easier.

* New Layout: We did a complete redesign of alfred3's page layout, moving
  to Bootstrap v4.5 and making the layout responsive to screen size. This
  introduces the possibility for participants to use their mobile devices
  for completing alfred experiments - an important feature nowadays. Of
  course, experimenters can choose to turn off responsiveness if their
  experiments require a fixed layout.

* Documentation and tutorials for alfred3's most important features
  is now available: [Link to docs](https://jobrachem.github.io/alfred_docs/html/index.html)

* Integrated list randomization: We integrated the possibility for smart list
  randomization directly into alfred3 through `alfred3.ListRandomizer`,
  thereby offering a remarkably simple way for efficient randomization.

* Movement history: Alfred3 can now record detailed information about
  participants' movements in an experiment, such as the duration of
  individual visists to a page.

## alfred3 v1.4

### Added v1.4

With this version, alfred3 gains some powerful new features. This is the overview:

* The `UnlinkedDataPage` can be used to safely collect data that cannot be linked to any specific experiment session.
* Alfred3 now automatically generates a comprehensive, machine-readable codebook that describes your data set.
* Alfred3 now offers functionality for transforming locally collected data from .json to .csv format (both automatically at the end of each session, and manually via a command line interface).
* New hooks for pages and sections make it easier to tidily organize experiment code.

Details below!

#### New page classes

* `page.UnlinkedDataPage` : Use this page to collect data that should not be linkeable to the experiment data. All data from UnlinkedDataPages will be shuffled and saved in a separate file. No timestamps or other metadata are stored that would make it possible to link an unlinked dataset to an experiment dataset. Otherwise, usage is fully equivalent to ordinary pages.
* `page.CustomSavingPage` : This is an abstract page class for advanced users. It grants you detailed control over the saving behavior of your page. Basically, you give the page its own saving agent and manually define exactly, which data will be saved. For more information, call `help(CustomSavingPage)` .

#### Automatic codebook generation

Alfred now automatically generates a raw codebook from your experiment. The codebook contains descriptions for all user-input elements and can be exported as .csv or .json.

#### Automatic transformation of local data to .csv

Upon completion of an experiment session, alfred now automatically converts experiment data (including unlinked and codebook data) to .csv by default. You can control this behavior through the following options in config.conf:

``` ini
[general]
transform_data_to_csv = true # controls, whether to transform data or not
csv_directory = data # the .csv files will be placed in this directory
csv_delimiter = ; # Controls the delimiter. Default is semicolon.
```

#### Command line interface for exporting alfred3 data

Through a new command line interface, you can export alfred data, both from your local `save` directory, and from your MongoDB storage. Standard usage is to call the CLI from your experiment directory. It automatically extracts the relevant data from your config.conf or secrets.conf.

```

python3 -m alfred3.export --src=local_saving_agent
```

Detailed description of all parameters (available also from the terminal via `python3 -m alfred3.export --help` )

```

Usage: export.py [OPTIONS]

Options:
  --src TEXT           The name of the configuration section in 'config.conf'
                       or 'secrets.conf' that defines the SavingAgent whose
                       data you want to export.  [default: local_saving_agent]

  --directory TEXT     The path to the experiment whose data you want to
                       export. [default: Current working directory]

  -h, --here           With this flag, you can indicate that you want to
                       export .json files located in the current working
                       directory.  [default: False]

  --data_type TEXT     The type of data that you want to export. Accepted
                       values are 'exp_data', 'unlinked', and 'codebook'. If
                       you specify a 'src', the function tries to infer the
                       data type from the 'src's suffix. (Example:
                       'mongo_saving_agent_codebook' would lead to 'data_type'
                       = 'codebook'. If you give a value for 'data_type', that
                       always takes precedence. If no data_type is provided and
                       no data_type can be inferred, 'exp_data' is used.

  --missings TEXT      Here, you can manually specify a value that you want to
                       insert for missing values.

  --remove_linebreaks  Indicates, whether linebreak characters should be
                       deleted from the file. If you don't use this flag (the
                       default), linebreaks will be replaced with spaces.
                       [default: False]

  --delimiter TEXT     Here, you can manually specify a delimiter for your
                       .csv file. You need to put the delimiter inside
                       quotation marks, e.g. like this: --delimiter=';'.
                       [default: ,]

  --help               Show this message and exit.
```

#### New page hooks for more control

All page classes now provide the possibility to define additional hooks, granting you more fine-grained control over the exact time your code gets executed. Here is a list of them:

| Hook            | Explanation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `on_exp_access` | Hook for code that is meant to be executed as soon as a page is added to an experiment. This is your go-to-hook, if you want to have access to the experiment, but don't need access to data from other pages.                                                                                                                                                                                                                                                                                                                                    |
| `on_first_show` | Hook for code that is meant to be executed when a page is shown for the first time. This is your go-to-hook, if you want to have access to data from other pages within the experiment, and your code is meant to be executed only once (i.e. the first time a page is shown).                                                                                                                                                                                                                                                                    |
| `on_each_show` | Hook for code that is meant to be executed *every time* the page is shown.                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `on_first_hide` | Hook for code that is meant to be executed only once, when the page is hidden for the first time, **before** saving the page's data. **Important**: Note the difference to `on_close` , which is executed upon final submission of the page's data. When using `on_first_hide` , subject input can change (e.g., when a subject revists a page and changes his/her input).                                                                                                                                                                                                                                                                                                   |
| `on_each_hide` | Hook for code that is meant to be executed *every time* the page is hidden, **before** saving the page's data.                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `on_close` | Hook for code that is meant to be executed when a page is closed. This is your go-to-hook, if you want to have the page execute code only once, when submitting the data from a page. Closing happens, when you leave a page for the first time in a `HeadOpenSection` (participants can revisit the page, but can't change their input), and when you leave a page in a `SegmentedSection` (participants cannot go back to previous pages). That means, this hook has no effect inside a standard `Section` , because its pages don't get closed. |

For now, the old hooks `on_showing` , `on_showing_widget` (both equivalent to `on_each_show` ) and `on_hiding` , as well as `on_hiding_widget` (both equivalent to `on_each_hide` ) will still work but are deprecated and will be removed in future versions. Therefore we ask you to use the new hooks from now on.

Here is an example:

``` python
from alfred3.page import Page
from alfred3.element import TextElement

class Welcome(Page):
    def on_exp_access(self):
        self += TextElement("This code is executed upon adding the page to the experiment.")

    def on_first_show(self):
        self += TextElement("This code is executed right before showing the page for the first time")

```

#### New section hooks for more control

The section classes also gain some hooks:

| Hook | Explanation |
| --- | --- |
| `on_exp_access` | Hook for code that is meant to be executed as soon as a section is added to an experiment. |
| `on_enter` | Hook for code that is meant to be executed upon entering a section in an ongoing experiment. |
| `on_leave` | Hook for code that is meant to be executed upon leaving a section in an ongoing experiment. This code will be executed *after* closing the section's last page. |

Here is an example:

``` python
from alfred3.section import Section
from alfred3.page import Page

class Main(Section):
    def on_exp_access(self):
        self += Page(title="Demo Page, added upon adding the section to the experiment.")

    def on_enter(self):
        print("Code executed upon entering the section.")
```

## alfred v1.3.1 (Released 2020-08-24)

### Fixed v1.3.1

* Fixed a bug in the template donwloading CLI.

## alfred v1.3.0 (Released 2020-08-19)

### Added v1.3.0

* We defined the *iadd* ( `+=` ) operator for all pages, sections and the experiment class. In many cases, it can replace a call to the `append()` method of these classes. Don't worry, the `append()` method is not going away. You can use this operator...
    - ... to append elements to a page
    - ... to append pages and sections to a sections
    - ... to append pages and section to the experiment

Simple examples:

``` python
# (assuming correct imports)

# Append element to a page
page = Page(title="Test Page")
page += TextElement("Testtext", name="text1")
```

``` python
# (assuming correct imports)
# Append page and section to a section
main = Section()

second = Section()
page = Page(title="Test Page")
second += page # using the page instance from the

main += second
```

``` python
# (assuming correct imports)
# Append sections and pages to the experiment
exp = Experiment()
main = Section()
exp += main
```

When using the `+=` operator in class definitions, you refer to "self":

``` python
# (assuming correct imports)

class Welcome(Page):
    def on_showing(self):
        self += TextElement("Testtext", name="text1")
```

### Changed v1.3.0

* When downloading a template, it is now allowed to have a `.idea` and a `.git` file already present in the target directory. Otherwise, the directory must be empty.

## alfred v1.2.1 (Released 2020-08-18)

### Fixed v1.2.1

* Fixed an underspecified filepath handling that caused trouble with the logging initialization under windows.

### Changed v1.2.1

* We made using the flask debugger easier:
    - If you use the command line interface, you can add the flag 'debug' to start an experiment in debugging mode and use flask's builtin debugging tools. The command becomes `python -m alfred3.run -debug` .
    - If you use the small `run.py` , you can pass `debug=True` as a parameter in `auto_run()` : `runner.auto_run(debug=True)`
* Upgraded the command line interface for downloading templates.
    - Most notably, the interface gained the flag '-h'/'--here', that you can use to indicate that you want the template's files to be placed directly in the '--path' (by default, in the current working directory).
    - Instead of the '-b'/'--big' and '-r'/'--runpy' flags, you can now choose between variants by setting the option '--variant' to 's', 'm' (default), or 'l'.
    - Enhanced handling of naming conflicts.
    - This is the full new usage:

```

Usage: template.py [OPTIONS]

Options:
  --name TEXT     Name of the new experiment directory.  [default:
                  alfred3_experiment]

  --path TEXT     Path to the target directory. [default: Current working
                  directory]

  --release TEXT  You can specify a release tag here, if you want to use a
                  specific version of the template.

  --variant TEXT  Which type of template do you want to download? The
                  available options are: 's' (minimalistic), 'm' (includes
                  'run.py' and 'secrets.conf') and 'b' (includes subdirectory
                  with imported classes and instructions.)  [default: m]

  -h, --here      If this flag is set to '-h', the template files will be
                  placed directly into the directory specified in '--path',
                  ignoring the paramter '--name'.  [default: False]

  --help          Show this message and exit.
  ```

## alfred v1.2.0 (Released 2020-07-13)

### Added v1.2.0

#### Minor changes v1.2.0

* You can now define an encryption key either in `secrets.conf` or in an environment variable named `ALFRED_ENCRYPTION_KEY` .

* We added a new page class `page.NoDataPage` , which does only return the page's tag and uid when queried by the saving agent. This will prevent any data from being saved to the standard saving agents. You can use this page, if you want to save data to an external database, separated from experimental data (e.g., if you need to save personal data).

* We added support for custom imports of `.py` files from subdirectories that are transferable to mortimer by including the package `thesmuggler` . If you want to store content in an external `.py` file (which we highly recommend, as it leads to a clearer directory structure), you can import such a file by using `thesmuggler.smuggle()` . Example:

```

# files/instructions.py

text = "This text resides in files/instructions.py"
```

```

# script.py
from thesmuggler import smuggle

inst = smuggle("files/instructions.py")

print(inst.text)
```

#### Fullscreen option for Google Chrome v1.2.0

We added an option that allows you to make experiments start in Chrome's fullscreen (or "kiosk") mode with hidden browser controls (forward, backward, refresh). This lowers the probability that subjects in lab experiments will mess with the browser controls. On Windows, it will only work, if Chrome is installed to a default directory and is only tested on Windows 10.

You can enable this option in your config.conf:

``` ini
[experiment]
fullscreen = true   # default: false
```

**In order for this feature to work, you need to use our most recent version of `run.py` . There is an easy way to do this (see below)**

Old `run.py` files will continue to work, but we strongly recommend to use the new method, because this will ensure that your experiment-running code will be updated together with alfred3.

#### `alfred3.run` module with command line interface v1.2.0

Added a module `alfred3.run` that contains the functionality for locally running alfred experiments. It can be used via the command line like this:

``` BASH
python3 -m alfred3.run
```

 Note that you must run this code from within your experiment directory, or specifiy a path to the experiment directory with the option `--path=<path>` . By setting the flag `-m` ( `--manual-open` ), you can switch off the automatic opening of a browser window upon experiment startup. See `python3 -m alfred3.run --help` for all available options.

You can also continue to use a `run.py` in your experiment directory to run your experiment, if you wish. From now on, this file should look like this (watch [this video](https://www.youtube.com/watch?v=sugvnHA7ElY) for an explanation concerning the `if __name__ == "__main__"` protector.):

``` Python
from alfred3.run import ExperimentRunner

if __name__ == "__main__":
    runner = ExperimentRunner()
    runner.auto_run()
```

This feature eliminates the need for a `run.py` file in your experiment directory. The API might still change in the future, so this feature is considered experimental.

If you want to gain more control over your run.py you can execute individual steps (*only recommended for advanced users. Usually, this will not be necessary.*):

``` python
from alfred3.run import ExperimentRunner

if __name__ == "__main__":
    runner = ExperimentRunner()
    runner.generate_session_id()
    runner.configure_logging()
    runner.create_experiment_app()
    runner.set_port()
    runner.start_browser_thread()
    runner.print_startup_message()
    runner.app.run(use_reloader=False, debug=False)
```

This will allow you to customize logging configuration or to extract the flask app that is created through your alfred experiment.

* The former can be achieved by configuring a logger of the name `exp.<exp_id>` , where `<exp_id>` is the experiment ID, accessible via `runner.config["exp_config"].get("metadata", "exp_id")`
* The latter can be achieved by assigning the returned value of `runner.create_experiment_app()` to an object, or by accessing `runner.app` after `create_experiment_app` was run.

#### `alfred3.template` command line interface for experiment template v1.2.0

We have a new convenience feature for accessing the latest experiment template. Just use your terminal to execute the following command:

``` bash
python3 -m alfred3.template
```

This will download the latest experiment template from GitHub to your current working directory, including a useful `.gitignore` that will automatically prevent your `secrets.conf` from being included in your git repository.

With the optional argument `--path` , you can hand over a directory path to be used instead of your current working directory.

Of course, you can still download the template manually from GitHub, if you prefer so.

Additional options allow for more flexibility. Take a look at them with the following command:

``` bash
python3 -m alfred3.template --help
```

### Changed v1.2.0

#### Enhanced configuration v1.2.0

* If you don't want to change the default configuration, you don't need a `config.conf` file in your experiment directory anymore.

* We separated the values provided in `config.conf` into two files to enable easier code sharing and enhance security at the same time:
    - `config.conf` from now on holds exclusively publicly available configuration. **This file is meant to be shared.**
    - `secrets.conf` is a new configuration file that only holds secret information like database credentials. **This file should never be shared.** It is included in the `.gitignore` of our experiment template to prevent accidental sharing.

* You can now supply your own custom configuration options via `config.conf` and `secrets.conf` . The experiment object gains a `config` and a `secrets` attribute, both of which are instances of a modified [configparser. ConfigParser](https://docs.python.org/3/library/configparser.html) and provided the same methods for accessing options.
    - Pay attention to the way that values are returned. `ConfigParser` objects don't guess the type of your values. Instead, they provide specialized methods. `get` returns *str*, `getint` returns *int*, `getfloat` returns *float*, and `getboolean` returns *boolean* values (which should be entered as "true"/"false" or "1"/"0" in `config.conf` ).
    - All of these methods take as first argument the section and as second argument the key (as demonstrated below).

Usage example of custom cofiguration:

``` ini
# config.conf
[my_section]
my_key = my_value
my_bool = true
```

``` python
# script.py
from alfred3 import Experiment, page, element

class Welcome(page.Page):

    def on_showing(self):
        my_value = self.experiment.config.get("my_section", "my_value")

        text = element.TextElement(my_value)
        self.append(text)

def generate_experiment(self, config=None):
    exp = Experiment(config=config)

    welcome = Welcome(title="Welcome page")

    if exp.config.getboolean("my_section", "my_bool"):
        exp.append(welcome)

    return exp
```

#### Enhanced logging v1.2.0

* All instances and children of `Experiment` ,           `element.Element` ,           `page.Page` , and `section.Section` gain a `log` attribute.
* The `log` attribute is basically a wrapper around a `logging.Logger` . It behaves like a normal logger in many ways, offering the usual methods `debug` ,           `info` ,           `warning` ,           `error` ,           `critical` ,           `exception` ,  `log` , and `setLevel` .
* If you want to access the logger object directly to apply more detailed configuration, you can do so via `log.queue_logger` .

See [logging documentation](https://docs.python.org/3/howto/logging.html#logging-levels) for more information on the levels and configuration.

Usage:

``` python
from alfred3 import Experiment, page

class Welcome(page.Page):
    def on_showing(self):
        self.log.info("This message will be logged on showing of the page")

def generate_experiment(self, config=None):
    exp = Experiment(config=config)

    exp.log.info("This message will be logged after initialization of the experiment.")

    welcome = Welcome(title="Welcome page")

    # Sets the log level to 'WARNING'
    # The message logged above in the 'on_showing' definition will therefore
    # not be logged, as it is of level 'info'
    welcome.log.setLevel("WARNING")

    exp.append(welcome)
```

### Removed v1.2.0

#### Removed qt-webkit support v1.2.0

We removed the option to run alfred experiments via qt-webkit. This was a rarely used feature and introduced a dependency on PySide2, which caused issues with  deployment via mortimer and mod_wsgi. Specifically, the following option in config.conf is no longer available:

We removed the option to run alfred experiments via qt-webkit. This was a rarely used feature and introduced a dependency on PySide2, which caused issues with  deployment via mortimer and mod_wsgi. Specifically, the following option in config.conf no longer has any effect:

``` ini
[experiment]
type = qt-wk
```

Instead, you can turn to the new option for running experiments in Google Chrome's fullscren (aka "kiosk") mode (see above).

## alfred3 v1.1.5 (Released 2020-05-13)

### Fixed v1.1.5

* Fixed a bug in the parsing of the auth_source parameter in `config.conf`

## alfred3 v1.1.4 (Released 2020-05-05)

### Announcement: Released to PyPi under the new name **alfred3**

* We are proud to announce that alfred is now available on PyPi. Because there already exists a package named "alfred", we decided to change the name to "alfred3" in celebration of the recent port to Python 3.

* Alfred3 can now be installed via pip:

```

pip install alfred3
```

* When alfred is installed via pip, you must change all imports in your `script.py` and `run.py` to the new name.

### Changed v1.1.4

* Changed name to alfred3 (see above).

* From now on, we will generally be using the changelog format recommended by [Keep a Changelog](https://keepachangelog.com/en/)
    - In the course of this change, we changed the name of the former `NEWS.md` to `CHANGELOG.md` .

## alfred v1.0.7

### Security improvements

* We further increased data protection and data security through an improved handling of access to the alfred database from inside web experiments deployed via  mortimer.
* Updated handling of local experiments: You can now specify an optional `auth_source` parameter in the `mongo_saving_agent` section in `config.conf` . The parameter will be passed to the `authSource` parameter of `pymongo.MongoClient` in the initialisation of the saving agent. This allows you to use database accounts that user other databases than "admin" for authentication, which offers greater security.

### Smaller changes

* Disabled the logging of debug messages for the `Page.on_showing()` method. This led to overcrowded logs.

## alfred v1.0.6

### Encryption

* In your script.py, you can now use symmetric encryption to encrypt your data. The encryption is performed with an instance of `cryptography.fernet.Fernet` , using a safe, user-specific unique key generated by mortimer (**v0.4.4+**).
    - **Encryption**: Encrypt data of types `str` , `int` , and `float` via `alfred.Experiment.encrypt()` . The method will return an encrypted version of your data, converted to string.
    - **Decryption**: Decrypt data of types `str` or `bytes` via `alfred.Experiment.decrypt()` . The method will return a decrypted version of your data, converted to string.
* **NOTE** that the saving agent will automatically save all data collected by elements (after the `on_hiding()` method is executed). You will need to encrypt data **before** they are saved in order to secure your data in the database.
* For offline testing, the Fernet instance will be initialized with the key `OnLhaIRmTULrMCkimb0CrBASBc293EYCfdNuUvIohV8=` . **IMPORTANT**: This key is public. Encrypted data in local (e.g., offline) experiments is not safe. This functionality is provided exclusively for testing your experiment before uploading to mortimer and running.

### Smaller changes and Bugfixes

* Pages now have a getter method for their experiment, i.e. you can access the experiment via `Page.experiment` , if the page has been added to an experiment instance at the time the method is called.
* Fixed the display of experimenter messages (e.g. a message that informs the participant about a minimum display time, if he or she tries to move to the next page too early)

## alfred v1.0.5

### Bugfixes v1.0.5

* fixed #37

### Minor changes v1.0.5

* rename `PageController.change_to_finished_section` : This was a missed function call from the old naming scheme. Generally, it will not affect the user in most cases, but it still exists as a deprecated function, logging a warning now.


## alfred v1.0.4

### Bugfixes v1.0.4

* This includes a hotfix for an issue with ALfred v1.0.3.

### Minor changes v1.0.4

* Local saving agent now checks, whether the path given in config.conf is absolute. If not, the agent treats it as a relative path, relative to the experiment directory.
* Alfred now saves its the version number alongside each saved dataset, so that the used version can be identified.

## alfred v1.0.3

### Bugfixes v1.0.3

* This includes a hotfix for an issue with Alfred v1.0.2

## alfred v1.0.2

### Bugfixes v1.0.2

* Fixed a bug in `localserver.py` that caused trouble for videos implemented via `alfred.element.WebVideoElement` in Safari (wouldn't play at all) and Chrome (forward/backward wouldn't work)

### Other changes v1.0.2

* `alfred.element.WebVideoElement` :
    - New parameter `source` : A filepath or url that points to the video ( `str` ).
    - New parameter `sources_list` : A list of filepaths and/or urls that point to the video, use this if you want to include fallback options in different formats or from different sources ( `list` of `str` elements).
    - The parameters `mp4_path` , `mp4_url` , `ogg_path` , `ogg_url` , `web_m_path` , and `web_m_url` are replaced by `source` . They still work, but will now log a deprecation warning.
    - New parameter `muted=False` : If `True` , the video will play with muted sound by default.
    - The parameter `width` now defaults to `width=720` .
    - Disabled the right-click context menu for videos included via `alfred.element.WebVideoElement`
    - Disabled video download for videos implemented via `alfred.element.WebVideoElement` (was only possible in Chrome).
* `Page` gets a new parameter `run_on_showing` , which defaults to `run_on_showing='once'` . This means, by default a Page executes the `on_showing` method only when it is shown for the first time. This behavior can be altered by setting the new parameter to `run_on_showing='always'` . The latter can lead to duplicate elements on a page, if a subject goes backward inside an experiment, which will be unwanted behavior in most cases.

## alfred v1.0.1

### Bugfixes v1.0.1

* Fixed a bug that caused a mixup with filepaths for web experiments hosted with mortimer.

## alfred v1.0

### Breaking changes v1.0

#### Port to Python 3

* One of the most important changes for us is the port from Python 2.7 to Python 3, which will ensure ongoing support for the coming years.
* You can find key differences listed here: [https://docs.python.org/3.0/whatsnew/3.0.html](https://docs.python.org/3.0/whatsnew/3.0.html)
    - All strings in Python 3 are unicode by default. In Python 2.7, strings with umlauts like ä, ö or ü needed to be preceded by a u to turn them into unicode-strings: `u"Example strüng."` . This often lead to unnecessary errors and is not necessary anymore.
    - Printing works a little differently. You used to be able to print output to the console with a command like `print "this string"` . This syntax is now deprecated and will throw an error. From now on, you need to use the print statement like any normal function: `print("this string")` .

#### New class names

* `Page` replaces `WebCompositeQuestion`
* `Section` replaces `QuestionGroup`
* `SegmentedSection` replaces `SegmentedQG`
* `HeadOpenSection` repladces `HeadOpenQG`
* These changes should clarify the functionality of the corresponding classes.

#### Switch from `lowerCamelCase` to `underscore_case`

* Throughout alfreds complete code base, we switched from `lowerCamelCase` to `underscore_case` .**ATTENTION: This affects almost every line of code!**
* This change reflects our effort to adhere to PEP 8 Styleguide ([PEP - click for more info](https://www.python.org/dev/peps/pep-0008/)). Some excerpts:
    - Class names should normally use the CapWords convention.
    - Function names should be lowercase, with words separated by underscores as necessary to improve readability.
    - Variable names follow the same convention as function names.
    - Method names and instance variables: Use the function naming rules: lowercase with words separated by underscores as necessary to improve readability.

#### New names for existing features

* `Page.on_showing()` replaces `WebCompositeQuestion.onShowingWidget()` (Alfred v0.2b5 name).
* `Page.append()` replaces `WebCompositeQuestion.addElement()` and `WebCompositeQuestion.addElements()` (Alfred v0.2b5 names).
* `Page.get_page_data()` is a new shortcut for `WebCompositeQuestion._experiment.dataManager.findExperimentDataByUid()` (Alfred v0.2b5 name), a method for accessing data from a previous page inside an `on_showing` hook.
* `Section.append()` replaces `QuestionGroup.appendItem()` and `QuestionGroup.appendItems()` (Alfred v0.2b5 names).
* `Experiment.append()` replaces `Experiment.questionController.appendItem()` and `Experiment.questionController.appendItems()` (Alfred v0.2b5 names).
* `Experiment.change_final_page()` is a new shortcut for `Experiment.pageController.appendItemToFinishQuestion()` (Alfred v0.2b5 name), a method for changing the final page of on exp.

#### Experiment metadata

* There is a new section `[metadata]` in `config.conf` , which includes the following information:
    - `title` : The experiment title (previously called experiment name)
    - `author` : The experiment author
    - `version` : The experiment version
    - `exp_id` : The experiment ID (**IMPORTANT:** This ID is used to identify your experiment data, if you set up a local alfred experiment to save data to the mortimer database. It is not used, if you deploy your experiment as a web experiment via mortimer.)
* `alfred.Experiment` no longer takes the arguments `expType` ,           `expName` and `expVersion` . Instead, these metadata are now defined in the `config.conf` , section `[metadata]` .
* To process metadata in mortimer, the following changes need to be implemented in `script.py` :
    - `def generate_experiment(config=None)` (the function gets a new parameter `config` , which defaults to `None` )
    - `exp = Experiment(config=config)` (the experiment should be initialized with the parameter `config` , defaulting to `config` , which gets handed down from the `generate_experiment` function.)

#### File import

* Importing a file from the project directory now **always** needs to take place within the `generate_experiment()` function. This is necessary for compatibility with the newest version of mortimer. This way, we can handle multiple resources directories.

### New Features v1.0

#### Define navigation button text in `config.conf`

* `config.conf` gets a new section `[navigation]` that lets you define `forward` ,           `backward` , and `finish` button texts.

#### New recommended `script.py` style

* Removed the need to define a script class ( `class Script(object)` ), saving one layer of indentation
* Removed the need to end a script with `generate_experiment = Script().generate_experiment`
* Removed the need to define `expName` and `expVersion` inside script
* Recommended style: Define a new class for every page in your experiment. This has a couple of advantages:
    - No difference between defining static pages and dynamic pages anymore. This lowers the hurdle for creating dynamic experiments.
    - Separation of experiment structure and experiment content is enhanced, which should clarify the `script.py`
    - Code reuse is facilitated (Pages can be reused)

Example:

``` python
# -*- coding:utf-8 -*-
from alfred import Experiment
from alfred.page import Page
import alfred.element as elm
import alfred.section as sec

class HelloWorld(Page):
    def on_showing(self):
        hello_text = elm.TextEntryElement('Please enter some text.')
        self.append(hello_text)

def generate_experiment(self, config):
    exp = Experiment(config=config)

    hello_world = HelloWorld(title='Hello, world!')

    main = sec.Section()
    main.append(hello_world)

    exp.append(main)
    return exp
```

#### Increased security for local experiments

* We implemented a three-step process to access database login data. The first two options make it much safer to share your code, e.g.on the OSF, because you don't have to worry about accidentally sharing secrets anymore.
    - Provide login data in environment variables (new, recommended)
    - Provide encrypted login data in `config.conf` (new, recommended)
    - Provide raw login data in `config.conf` (**not recommended**, use only for testing)
* If your databse is correctly equipped with a valid commercial SSL certificate, you can now set the option `use_ssl = true` in the section `[mongo_saving_agent]` of your `config.conf` to enable a secure connection via SSL. You can also use self-signed SSL certificates, if you set the option `ca_file_path` to the file path of your Certificate Authority (CA) public key file (often a .pem file).

#### `Page.values`

* `Page.values` is a dictionary that serves as a container for pages. You can use it for example to create pages using loops and if-statements. More on how to use it can soon be found in the wiki. It is a special dictionary that allows for element access (reading and writing) via dot-notation.

Example:

``` python
# (imports)

class Welcome(Page):
    def on_showing(self):
        text01 = TextElement(self.values.text01, name='text01')
        self.append(text01)

def generate_experiment(self, config=None):
    exp = Experiment(config=config)

    page = Welcome(title='page01', uid='page01')
    page.values.text01 = 'text01'

    exp.append(page)
    return exp

```

### Deprecated v1.0

| Deprecated function (alfred v0.2b5 name)  | Replaced by |
| ------------- | ------------- |
| `WebCompositeQuestion.onShowingWidget()` | `Page.on_showing()` |
| `WebCompositeQuestion.onHidingWidget()` | `Page.on_hiding()` |
| `WebCompositeQuestion.addElement()` | `Page.append()` |
| `WebCompositeQuestion.addElements()` | `Page.append()` |
| `QuestionGroup.appendItem()` | `Section.append()` |
| `QuestionGroup.appendItems()` | `Section.append()` |
| `Experiment.questionController.appendItem()` | `Experiment.append()` |
| `Experiment.questionController.appendItems()` | `Experiment.append()` |

### Bug fixes and other changes v1.0

* **Improved handling of browser commands.** In web experiments, subjects used to be able to cause trouble by using the browser controls (forward, backward, refresh) instead of the experiment controls at the bottom of the page to move through an experiment. In some cases, this could render the subject's data unusable. Now, when a subject uses the browser controls, Alfred will always return the current state of the experiment. This way, no more data should be lost.
* **Fixed a saving agent bug.** When quickly moving through an experiment, the saving agent sometimes didn't complete it's tasks correctly and basically crashed. This does not happen anymore.

### Removed features v1.0

* **No more pure QT experiments.** We completely removed pure QT experiments from the framework. Those have recently seen very little use and have some drawbacks compared to web experiments and qt-webkit (qt-wk) experiments.
