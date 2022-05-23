How to use loops
=============================

Loops allow us to perform enormous numbers of similar actions that differ
only in details. Here, we provide a basic example experiment and go into
some more details for explaining how to loop over files in a second example
in the second section. In a third section, we will build on our example
from section two and talk about shuffling pages in a section.

Example experiment
--------------------

This is an example experiment that employs a loop::

    import alfred3 as al
    exp = al.Experiment()

    rivers = ["Themse", "Rhein", "Ems"]

    @exp.member
    class Main(al.Section):
        shuffle = True

        def on_exp_access(self):
            for item in range(3):
                self += Task(name=f"taskpage_item_{item + 1:02}", vargs={"i": item})


    class Task(al.Page):

        def on_first_show(self):
            item = self.vargs.i
            stimulus = rivers[item]

            self.title = f"Task {item}"

            self += al.Text("Please estimate the length of the following river:", align="center")
            self += al.Text(f"**{stimulus}**", font_size="large", align="center")

            self += al.NumberEntry(placeholder="Enter a number", suffix="km", name=f"task_{item:02}")
            self += al.Value(stimulus, name=f"item_{position:02}")


    if __name__ == "__main__":
        exp.run()


Loop over files
-----------------

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

Next, we start by defining a page that displays the first of our images
along with two buttons for rating::

    import alfred3 as al
    exp = al.Experiment()

    @exp.member
    class ImagePage(al.Page):

        def on_exp_acess(self):
            self += al.Image(path="images/img1.png")

            self += al.SingleChoiceButtons(
            "Like it", "Don't like it",
            toplab="How do you feel about this picture?",
            name="img_rating_1"
            )

Now we could easily copy and paste this code three times and use this
technique to display all our trials. But coding like this becomes tedious
and inefficient very quickly. It is much  more efficient to use a loop
and let the computer do the work.

To add pages via loops, we use sections. First, we simply add our section
and add our page to the section in the section's *on_exp_access* hook::

    import alfred3 as al
    exp = al.Experiment()


    @exp.member
    class ImageSection(al.Section):

        def on_exp_access(self):
            self += ImagePage(name="img_page_1")


    class ImagePage(al.Page):

        def on_exp_acess(self):
            self += al.Image(path="images/img1.png")

            self += al.SingleChoiceButtons(
            "Like it", "Don't like it",
            toplab="How do you feel about this picture?",
            name="img_rating_1"
            )


Now we want to create a loop in the section's *on_exp_access* hook to
add three ImagePages. Page names must be unique, we use the loop's index
and f-strings for giving different names to our pages. Note that

1. We add 1 to the index, because Python starts counting at 0, but we
   want to start counting at 1 for the purpose of our page names.
2. We add ``:02`` to the f-string to add a leading zero to the index
   number. This will simply help us in sorting down the road in data
   analysis.

Here's the code. This will not run; below we explain, why::

    import alfred3 as al
    exp = al.Experiment()


    @exp.member
    class ImageSection(al.Section):

        def on_exp_access(self):
            for index in range(3):
            self += ImagePage(name=f"img{index+1:02}")


    class ImagePage(al.Page):

        def on_exp_acess(self):
            self += al.Image(path="images/img1.png")

            self += al.SingleChoiceButtons(
            "Like it", "Don't like it",
            toplab="How do you feel about this picture?",
            name="rating_1"
            )

Now we have a problem: Element names must be unique aswell, so we
will get an error message::

    alfred3.exceptions.AlfredError: Element name 'rating_1' is already present in the experiment.

To solve this problem, we will again use the loop index that we used
to give our pages unique names. This case is a little different, however,
because we are adding our SingleChoiceButtons element in the *page's*
*on_exp_access* hook, not in the *section's*. To make the index available
to the ImagePage, we can use the page's *vargs* argument. This allows us
to pass a dictionary to a page upon initialization. The values of this
dictionary are then available via dot notation through ``Page.vargs``.
We can use this to count up in the element names. This is how it
looks in practice::

    import alfred3 as al
    exp = al.Experiment()


    @exp.member
    class ImageSection(al.Section):

        def on_exp_access(self):
            for index in range(3):
                self += ImagePage(name=f"img{index+1:02}", vargs={"index": index})


    class ImagePage(al.Page):
        prefix_element_names = True

        def on_exp_acess(self):
            index = self.vargs.index

            self += al.Image(path="images/img1.png")

            self += al.SingleChoiceButtons(
            "Like it", "Don't like it",
            toplab="How do you feel about this picture?",
            name=f"rating_{index + 1:02}"
            )

Now our experiment will run and our ratings will have the correct names.
But we see the same image on all pages! So we need to apply the same strategy
as before, using the loop index in the definition of our image path::

    import alfred3 as al
    exp = al.Experiment()


    @exp.member
    class ImageSection(al.Section):

        def on_exp_access(self):
            for index in range(3):
                self += ImagePage(name=f"img{index+1:02}", vargs={"index": index})


    class ImagePage(al.Page):
        prefix_element_names = True

        def on_exp_acess(self):
            index = self.vargs.index

            self += al.Image(path=f"images/img{index}.png")

            self += al.SingleChoiceButtons(
            "Like it", "Don't like it",
            toplab="How do you feel about this picture?",
            name=f"rating_{index + 1:02}"
            )

Et voilá - our looped section with image ratings complete.

Shuffle the order of pages
----------------------------

In some studies, you may wish to show the pages in a section in a random
order. Alfred3 has got you covered for this, but we will start with a
warning:

.. warning::
    Whenever you show pages in a random order, you must take some things
    into account.

    1. You have to keep track of the actual order that participants
       are presented with. This will allow you to identify effects of
       the position of a page or stimulus on a page. The method
       :meth:`.Page.position_in_section` is very useful for this.

    2. You have to keep track of the actual material that was presented
       to participants on each page. This will allow you to identify
       effects of the concrete material used on a page. A page's
       *vargs* argument is very useful for this purpose.

    3. You should think about which attribute (order or identity of the
       stimulus) is more important for you when naming elements.

    4. To keep the codebook, that alfred3 automatically creates for you,
       consistent, you have to ensure that each element name is associated
       with *stable* settings in terms of labels, placeholders, force_input,
       and so on.

    5. Test your experiment data diligently to make sure that all
       necessary information is saved.


.. danger::
    If you do not take the above warning seriously, you WILL mess up your
    data, lose time and become quite upset.

Shuffling itself is easy. Just add ``shuffle = True`` to a section, and
its pages will be shown in random order::

    import alfred3 as al
    exp = al.Experiment()


    @exp.member
    class ImageSection(al.Section):
        shuffle = True

        def on_exp_access(self):
            for index in range(3):
                self += ImagePage(name=f"img{index+1:02}", vargs={"index": index})


    class ImagePage(al.Page):
        prefix_element_names = True

        def on_exp_acess(self):
            index = self.vargs.index

            self += al.Image(path=f"images/img{index}.png")

            self += al.SingleChoiceButtons(
            "Like it", "Don't like it",
            toplab="How do you feel about this picture?",
            name=f"rating_{index + 1:02}"
            )


Save order of creation in element names
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this case, however, we lose the information about the actual order that
specific participants saw. Let's solve this problem by using the
:meth:`.Page.position_in_section` method and a :class:`.Value` element.
With this combination, we can save the order that our pages appeared
in.

**IMPORTANT**: We also have to think about the time in the experiment at
which our code is executed. In the previous code examples, we have
constructed our ImagePage class in the *on_exp_access* hook, which
was fine until now. Now, however, we need to be aware that the section
will shuffle its pages *when we enter the section*, which is later than
the execution of our page's *on_exp_access**. To deal with this, we
change the construction of our page to an *on_first_show* hook::

    import alfred3 as al
    exp = al.Experiment()


    @exp.member
    class ImageSection(al.Section):
        shuffle = True

        def on_exp_access(self):
            for index in range(3):
                self += ImagePage(name=f"img{index+1:02}", vargs={"index": index})


    class ImagePage(al.Page):
        prefix_element_names = True

        def on_first_show(self): # change to on_first_show
            index = self.vargs.index
            position = self.position_in_section() # get position

            self.title = f"Task {position}" # use page position to give sensible title

            self += al.Image(path=f"images/img{index + 1}.png")

            self += al.SingleChoiceButtons(
            "Like it", "Don't like it",
            toplab="How do you feel about this picture?",
            name=f"rating_img{index + 1:02}"
            )

            # we *save* position, and include the index of the
            # corresponding image in the *name*
            self += al.Value(position, name=f"position_img{index + 1:02}")

If we save our data like this, we have all information that we need.
Let's recap and connect to our warning from above:

1. We can identify which image a rating belongs to: "rating_img01" will
   refer to "img1", and so on, because the order in which we created
   the pages in the for-loop corresponds to the actual images.
2. We can identify the order of our pages: In our output data, we
   will have a variable "position_img01" that will tell us, at which
   position "img1" was shown. For example, if "position_img01" is "3",
   the file "img1" was shown on the third page to this participant.
3. Because we have used the image number in the name of our
   SingleChoiceButtons, our variable names
   will tell us about the *identity* of the presented image, not about
   its *position*. We have saved the position in its own variable.
4. We have ensured that our codebook is consistent, because our
   SingleChoiceButtons have constant labels and choice anchors.


Save order of appearance in element names
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We may wish to flip our saving strategy by saving the *order of appearance*
in variable names and the *stimulus identity* in its own variable.
To do this, we flip the use of the "index" and "position"
variables in the *on_fist_show* hook like this::

    import alfred3 as al
    exp = al.Experiment()


    @exp.member
    class ImageSection(al.Section):
        shuffle = True

        def on_exp_access(self):
            for index in range(3):
                self += ImagePage(name=f"img{index+1:02}", vargs={"index": index})


    class ImagePage(al.Page):
        prefix_element_names = True

        def on_first_show(self):
            index = self.vargs.index
            position = self.position_in_section() # get position

            self.title = f"Task {position}" # use page position to give sensible title

            self += al.Image(path=f"images/img{index + 1}.png")

            self += al.SingleChoiceButtons(
            "Like it", "Don't like it",
            toplab="How do you feel about this picture?",
            name=f"rating_trial{position:02}"
            )

            # we *save* position, and include the index of the
            # corresponding image in the *name*
            self += al.Value(f"img{index}.png", name=f"filename_img_trial{position:02}")


1. We can identify which image a rating belongs to through the Value element
   that we saved. For instance, "filename_img_trial01" will tell us the
   filename of the image that was shown on the first page to a certain
   participant.
2. We can identify the order of our pages through the variable names:
   The variable "rating_trial01" will contain the rating that a participant
   gave on the first page that they saw.
3. Because we have used the order of appearance in the name of our
   SingleChoiceButtons, our variable names
   will tell us about the *position* of the presented image, not about
   the actual image that was presented. We have saved the image's identity
   in its own variable.
4. We have ensured that our codebook is consistent, because our
   SingleChoiceButtons have constant labels and choice anchors.
