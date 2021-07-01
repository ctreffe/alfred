![GitHub](https://img.shields.io/github/license/ctreffe/alfred) [![zenodo](https://zenodo.org/badge/150700371.svg)](https://zenodo.org/badge/latestdoi/150700371)
# Welcome to alfred3 

Alfred3 is a package for Python 3 offering an easy way to create
computer experiments that meet the highest standards of Open Science.
Specifically, experiments created with alfred3 are transparent,
accessible, reproducible, and adhere to the [FAIR principles for
research software](https://www.doi.org/10.3233/DS-190026). In its core
version, alfred3 comes well-equipped for the creation of dynamic
content that can be delivered online via a webserver or offline running
on local machines. In addition, the [alfred3-interact
plugin](https://github.com/jobrachem/alfred3-interact) enables users to
create interactive group experiments with features such as automated
group forming, quick access to members' experiment data, and a
prepacked chat functionality.

Further advantages include:

* All alfred3 scripts are written in [Python
  3](https://www.python.org/), a very popular open source programming
  language that is easy to learn and fast to develop with, as it
  focuses on code readability. Thus, even minimal programming skills
  are sufficient to create experiments with alfred3 (see the
  requirement section for more details and suggestions on beginner
  tutorials).
* Alfred3 uses the principle of Object-oriented programming (OOP) to
  maximize code reusability. By simply copying and pasting elements
  between scripts, users can instantly integrate content from previous
  experiments with their current project.
* Experimenters can share experiments created with alfred3 the same way
  they share code from their data analysis. In addition to highly
  reusable code, transparency and ease of sharing are two key
  advantages of using script-based experimental software.
* Using open source software is a core principle of Open Science and
  both Python 3 and alfred3 are published under permissive open source
  licenses. Researchers will not face the hurdles associated with
  closed source software when trying to reproduce an alfred3 experiment
  (see [The Open Science Training
  Handbook](https://open-science-training-handbook.gitbook.io/book/open-science-basics/open-research-software-and-open-source)
  for more information on the importance of using open source research
  software for your experiments and data analyses).
* Online experiments written in alfred3 support all types of mobile
  devices through a responsive interface, making them suitable for a wide range of applications and settings (e.g., laboratory experiments where users are invited to bring their own devices, or surveying passers-py with tablets in public spaces)
* Alfred3 is optimized for the collection of personal data in full
  compliance with both the GDPR and official German guidelines on data
  management in psychological science ([English
  version](https://www.dgps.de/fileadmin/documents/Empfehlungen/Data_Management_eng.pdf)
  | [German
  version](https://www.dgps.de/fileadmin/documents/Empfehlungen/Datenmanagement_deu.pdf)).
  The core version of alfred3 already includes data encryption and
  decryption methods as well as unlinked storage options for personal or
  sensitive data (meaning that you can store personal data separately
  without the possibility of linking it back to experimental data).

## Installation

If you have Python 3.7 or newer installed, just install alfred3 via pip

```
$ pip3 install alfred3
```

## Documentation

Documentation and tutorials for alfred3's most important features
is available here: [Link to docs](https://alfredo3.psych.bio.uni-goettingen.de/docs/)

## A "Hello, world" experiment

Creating a hello-world experiment is as easy as writing this *script.py*
file. You can even do it in a simple text editor. Note that the file
must be named ``script.py``

```python
import alfred3 as al
exp = al.Experiment()
exp += al.Page("Hello, world!", name="hello_world") 
```

To run the script, open a terminal and change the working directory to
your experiment directory:

```
$ cd path/to/experiment
```

Next, simply execute the following command in the terminal::

```
$ alfred3 run
```

If you have *Google Chrome* installed on your machine, a browser window 
with the experiment opens automatically. Otherwise, open any webbrowser 
and visit ``http://127.0.0.1:5000/start`` to start the experiment.

Of course, this "Hello, world" experiment does not contain much content:
Only a single page with a heading. To learn how to add content to an 
experiment, visit our tutorials in the [alfred3 documentation](
https://alfredo3.psych.bio.uni-goettingen.de/docs/).

## Citation

**If you are publishing research conducted using alfred3, the 
following citation is required:**

>Treffenstaedt, C., Brachem, J., & Wiemann, P. (2021). Alfred3 - A 
library for rapid experiment development (Version x.x.x). Göttingen, 
Germany: https://doi.org/10.5281/zenodo.1437219

If you want to use alfred3 and need more information, don't hesitate to 
contact us via alfred@psych.uni-goettingen.de.

## alfred3 Mailing List

If you want to stay up to date with current developments, you can join 
our [mailing list](mailto:https://listserv.gwdg.de/mailman/listinfo/Alfred).
We use this list to announce new releases and spread important 
information concerning the use of Alfred. You can expect to receive at 
most one mail per month.
