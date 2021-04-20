How to use loops
=============================

Loops allow us to perform enormous numbers of similar actions that differ
only in details, while using minimal code. 

Let's say you want your participants to rate a number of pictures, and 
each picture should appear on a separate page. The pictures are in a 
subdirectory of your experiment directory named *images*. So your 
experiment directory might look like this::

    /images
        img1.png
        img2.png
        img3.png
    script.py

You can use the class style of writing a section to accomplish this 
goal with only a few lines of code for any number of images in the 
directory. We'll use the :meth:`.Section.on_exp_access` hook for this
purpose and walk through the process step by step.

First, we import alfred3 and instantiate the experiment::
    
    import alfred3 as al
    exp = al.Experiment()

Next, we derive the section and use the :meth:`.Experiment.member`
decorator to signal alfred3 that it belong to the experiment. We can use
any name for it, but it must be unique throughout the experiment. If
we want to randomize the order of the pages in this section, we can also
define the section's *shuffle* attribute::

    @exp.member
    class ImageSection(al.Section): 
        shuffle = True

Next, we start overloading (i.e. redefining) the 
:meth:`.Section.on_exp_access` hook::

    @exp.member
    class ImageSection(al.Section): 
        shuffle = True
        
        def on_exp_access(self):
            pass

Now we'll dive into the method definition. This is where we add the pages.
First, we'll make the image directory easily accesible to us. We have to
make sure that alfred3 knows that it's a subdirectory of the experiment
directory::

    def on_exp_access(self):
        img_dir = self.exp.path / "images"

Now, we start writing the loop. To loop through the content of our 
directory, we can utilize the fact that our *img_dir* variable is actually
a :class:`~pathlib.Path` object, which offers the method 
:meth:`~pathlib.Path.iterdir`. It loops over all files in the directory
and gives us a :class:`~pathlib.Path` object for each of them in the
iterations of our loop::

    def on_exp_access(self):
        img_dir = self.exp.path / "images"

        for img in img_dir.iterdir():
            pass

Here, we need to keep in mind, that all our pages and input elements 
need unique names. To achieve this, we use the builtin function 
:func:`enumerate` around our call to *iterdir*. It simply equips us with
one additional value per iteration, which is a simply counter. By 
default it starts counting at 0. In this case, we want it to start at 1,
so we enter a 1 as the second argument::

    # notice that we 'collect' two values here at the start: i, img
    # i is the counter
    for i, img in enumerate(img_dir.iterdir(), 1):
            pass

Within the loop, we now create a page, add the image and a SingleChoice
element to the page. Note that we use Python's f-string syntax to create
page and element names that include the counter. That makes them uniquely
identifiable. Note also, that we use the square-bracket syntax here
to refer to the pages as members of the section. The last thing we
do in this code block is saving the image's name as a value to the
page - because we need to make sure that we can adequately connect the 
collected data to the respective image::

    
    for i, img in enumerate(img_dir.iterdir(), 1):
        page_name = f"img_page_{i}"
        self += al.Page(name=page_name)

        self[page_name] += al.Image(img) # page is accessed with square bracket syntax
        
        self[page_name] += al.SingleChoice(
            "Like it", "Don't like it", 
            toplab="How do you feel about this picture?",
            name=f"img_rating_{i}"
            )
        
        self[page_name] += al.Value(img.name, name=f"img_rating_{i}_target")


And now, let's put it all together. We have built a sophisticated 
experiment here, which can have any number of pages, depending on the
number of images in our folder, with less than 25 lines of code::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class ImageSection(al.Section):
        shuffle = True

        def on_exp_access(self):
            
            img_dir = self.exp.path / "images"

            for i, img in enumerate(img_dir.iterdir(), 1):
                
                page_name = f"img_page_{i}"
                self += al.Page(name=page_name)

                self[page_name] += al.Image(img)
                
                self[page_name] += al.SingleChoice(
                    "Like it", "Don't like it", 
                    toplab="How do you feel about this picture?",
                    name=f"img_rating_{i}"
                    )
                
                self[page_name] += al.Value(img.name, name=f"img_rating_{i}_target")