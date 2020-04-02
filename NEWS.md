# alfred v1.0.3

## Bugfixes

* This includes a hotfix for an issue with Alfred v1.0.2

# alfred v1.0.2

## Bugfixes

* Fixed a bug in `localserver.py` that caused trouble for videos implemented via `alfred.element.WebVideoElement` in Safari (wouldn't play at all) and Chrome (forward/backward wouldn't work)

## Other changes

* `alfred.element.WebVideoElement` :
    - New parameter `source` : A filepath or url that points to the video ( `str` ).
    - New parameter `sources_list` : A list of filepaths and/or urls that point to the video, use this if you want to include fallback options in different formats or from different sources ( `list` of `str` elements).
    - The parameters `mp4_path` , `mp4_url` , `ogg_path` , `ogg_url` , `web_m_path` , and `web_m_url` are replaced by `source` . They still work, but will now log a deprecation warning.
    - New parameter `muted=False` : If `True` , the video will play with muted sound by default.
    - The parameter `width` now defaults to `width=720` .
    - Disabled the right-click context menu for videos included via `alfred.element.WebVideoElement` 
    - Disabled video download for videos implemented via `alfred.element.WebVideoElement` (was only possible in Chrome).
* `Page` gets a new parameter `run_on_showing` , which defaults to `run_on_showing='once'` . This means, by default a Page executes the `on_showing` method only when it is shown for the first time. This behavior can be altered by setting the new parameter to `run_on_showing='always'` . The latter can lead to duplicate elements on a page, if a subject goes backward inside an experiment, which will be unwanted behavior in most cases.

# alfred v1.0.1

## Bugfixes

* Fixed a bug that caused a mixup with filepaths for web experiments hosted with mortimer.

# alfred v1.0

## Breaking changes

### Port to Python 3

* One of the most important changes for us is the port from Python 2.7 to Python 3, which will ensure ongoing support for the coming years.
* You can find key differences listed here: [https://docs.python.org/3.0/whatsnew/3.0.html](https://docs.python.org/3.0/whatsnew/3.0.html)
    - All strings in Python 3 are unicode by default. In Python 2.7, strings with umlauts like ä, ö or ü needed to be preceded by a u to turn them into unicode-strings: `u"Example strüng."` . This often lead to unnecessary errors and is not necessary anymore.
    - Printing works a little differently. You used to be able to print output to the console with a command like `print "this string"` . This syntax is now deprecated and will throw an error. From now on, you need to use the print statement like any normal function: `print("this string")` .

### New class names

* `Page` replaces `WebCompositeQuestion` 
* `Section` replaces `QuestionGroup` 
* `SegmentedSection` replaces `SegmentedQG` 
* `HeadOpenSection` repladces `HeadOpenQG` 
* These changes should clarify the functionality of the corresponding classes.

### Switch from `lowerCamelCase` to `underscore_case` 

* Throughout alfreds complete code base, we switched from `lowerCamelCase` to `underscore_case` .**ATTENTION: This affects almost every line of code!**
* This change reflects our effort to adhere to PEP 8 Styleguide ([PEP - click for more info](https://www.python.org/dev/peps/pep-0008/)). Some excerpts:
    - Class names should normally use the CapWords convention.
    - Function names should be lowercase, with words separated by underscores as necessary to improve readability.
    - Variable names follow the same convention as function names.
    - Method names and instance variables: Use the function naming rules: lowercase with words separated by underscores as necessary to improve readability.

### New names for existing features

* `Page.on_showing()` replaces `WebCompositeQuestion.onShowingWidget()` (Alfred v0.2b5 name).
* `Page.append()` replaces `WebCompositeQuestion.addElement()` and `WebCompositeQuestion.addElements()` (Alfred v0.2b5 names).
* `Page.get_page_data()` is a new shortcut for `WebCompositeQuestion._experiment.dataManager.findExperimentDataByUid()` (Alfred v0.2b5 name), a method for accessing data from a previous page inside an `on_showing` hook.
* `Section.append()` replaces `QuestionGroup.appendItem()` and `QuestionGroup.appendItems()` (Alfred v0.2b5 names).
* `Experiment.append()` replaces `Experiment.questionController.appendItem()` and `Experiment.questionController.appendItems()` (Alfred v0.2b5 names).
* `Experiment.change_final_page()` is a new shortcut for `Experiment.pageController.appendItemToFinishQuestion()` (Alfred v0.2b5 name), a method for changing the final page of on exp.

### Experiment metadata

* There is a new section `[metadata]` in `config.conf` , which includes the following information:
    - `title` : The experiment title (previously called experiment name)
    - `author` : The experiment author
    - `version` : The experiment version
    - `exp_id` : The experiment ID (**IMPORTANT:** This ID is used to identify your experiment data, if you set up a local alfred experiment to save data to the mortimer database. It is not used, if you deploy your experiment as a web experiment via mortimer.)
* `alfred.Experiment` no longer takes the arguments `expType` , `expName` and `expVersion` . Instead, these metadata are now defined in the `config.conf` , section `[metadata]` .
* To process metadata in mortimer, the following changes need to be implemented in `script.py` :
    - `def generate_experiment(config=None)` (the function gets a new parameter `config` , which defaults to `None` )
    - `exp = Experiment(config=config)` (the experiment should be initialized with the parameter `config` , defaulting to `config` , which gets handed down from the `generate_experiment` function.)

### File import

* Importing a file from the project directory now **always** needs to take place within the `generate_experiment()` function. This is necessary for compatibility with the newest version of mortimer. This way, we can handle multiple resources directories.

## New Features

### Define navigation button text in `config.conf` 

* `config.conf` gets a new section `[navigation]` that lets you define `forward` , `backward` , and `finish` button texts.

### New recommended `script.py` style

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

### Increased security for local experiments

* We implemented a three-step process to access database login data. The first two options make it much safer to share your code, e.g.on the OSF, because you don't have to worry about accidentally sharing secrets anymore.
    - Provide login data in environment variables (new, recommended)
    - Provide encrypted login data in `config.conf` (new, recommended)
    - Provide raw login data in `config.conf` (**not recommended**, use only for testing)
* If your databse is correctly equipped with a valid commercial SSL certificate, you can now set the option `use_ssl = true` in the section `[mongo_saving_agent]` of your `config.conf` to enable a secure connection via SSL. You can also use self-signed SSL certificates, if you set the option `ca_file_path` to the file path of your Certificate Authority (CA) public key file (often a .pem file).

### `Page.values` 

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

## Deprecated

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

## Bug fixes and other changes

* **Improved handling of browser commands.** In web experiments, subjects used to be able to cause trouble by using the browser controls (forward, backward, refresh) instead of the experiment controls at the bottom of the page to move through an experiment. In some cases, this could render the subject's data unusable. Now, when a subject uses the browser controls, Alfred will always return the current state of the experiment. This way, no more data should be lost.
* **Fixed a saving agent bug.** When quickly moving through an experiment, the saving agent sometimes didn't complete it's tasks correctly and basically crashed. This does not happen anymore.

## Removed features

* **No more pure QT experiments.** We completely removed pure QT experiments from the framework. Those have recently seen very little use and have some drawbacks compared to web experiments and qt-webkit (qt-wk) experiments.

