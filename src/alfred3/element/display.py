"""
Provides elements that display content.

.. moduleauthor: Johannes Brachem <jbrachem@posteo.de>
"""

import io

from datetime import datetime
from typing import Union
from pathlib import Path
from uuid import uuid4

from emoji import emojize
import cmarkgfm
from cmarkgfm.cmark import Options as cmarkgfmOptions

from .._helper import is_url
from .._helper import inherit_kwargs

from .core import jinja_env
from .core import Element
from .core import RowLayout
from .core import LabelledElement
from .input import SingleChoiceButtons



class VerticalSpace(Element):
    """
    The easiest way to add vertical space to a page.

    Args:
        space: Desired space in any unit that is understood by a CSS
            margin (e.g. em, px, cm). Include the unit (e.g. '1em').

    Examples:

        Example of vertical space added between two text elements::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    self += al.Text("Element 1")
                    self += al.VerticalSpace("100px")
                    self += al.Text("Element 2")

    """

    def __init__(self, space: str = "1em"):
        """Constructor method."""
        super().__init__()
        self.space = space

    @property
    def web_widget(self):
        
        # documented at baseclass
        return f"<div class='vertical-space-element' style='margin-bottom: {self.space};'></div>"

@inherit_kwargs
class Html(Element):
    """
    Displays html code on a page.

    Args:
        html: Html to be displayed.
        path: Filepath to a file with html code (relative to the
            experiment directory).
        
        {kwargs}

    Notes:
        This works very similar to :class:`.Text`. The most notable
        difference is that the *Text* element expects markdown, and
        therefore generally renders input text in a ``<p>`` tag. This
        is not always desirable for custom html, because it adds a
        margin at the bottom of the text.

        The *Html* element renders neither markdown, nor emoji shortcodes.

    Examples:
        Adding a simple div to the experiment::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    self += al.Html(html="<div id='mydiv'>Text in div</div>")

    """

    element_template = jinja_env.get_template("html/TextElement.html.j2")

    def __init__(
        self,
        html: str = None,
        path: Union[Path, str] = None,
        **element_args,
    ):

        """Constructor method."""
        super().__init__(**element_args)

        self.html_code = html if html is not None else ""
        self.path = path

        if self._html_code and self.path:
            raise ValueError("You can only specify one of 'html' and 'path'.")

    @property
    def html_code(self) -> str:
        """str: The element's html code"""
        if self.path:
            return self.experiment.subpath(self.path).read_text()
        else:
            return self._html_code

    @html_code.setter
    def html_code(self, html):
        self._html_code = html

    @property
    def template_data(self) -> dict:
        
        d = super().template_data
        d["text"] = self.html_code

        return d

@inherit_kwargs
class Text(Element):
    """
    Displays text.

    You can use `GitHub-flavored Markdown`_ syntax and common
    `emoji shortcodes`_ . Additionally, you can use html for
    advanced formatting.

    Args:
        text: Text to be displayed.
        path: Filepath to a textfile (relative to the experiment
            directory).
        width: Element width. Usage is the same as in
            :class:`Element`, but the Text element uses its own
            specific default, which ensures good readability in
            most cases on different screen sizes.
        emojize: If True (default), emoji shortcodes in the text will
            be converted to unicode (i.e. emojis will be displayed).
        {kwargs}

    Examples:
        A simple text element, including a 😊 (``:blush:``) emoji added
        to a page::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class HelloWorld(al.Page):
                name = "hello_world"

                def on_exp_access(self):
                    self += al.Text("This is text :blush:")


    .. _GitHub-flavored Markdown: https://guides.github.com/features/mastering-markdown/
    .. _emoji shortcodes: https://www.webfx.com/tools/emoji-cheat-sheet/
    """

    element_template = jinja_env.get_template("html/TextElement.html.j2")

    def __init__(
        self,
        text: str = None,
        path: Union[Path, str] = None,
        width: str = None,
        emojize: bool = True,
        render_markdown: bool = True,
        **kwargs,
    ):

        """Constructor method."""
        super().__init__(width=width, **kwargs)

        self._text = text if text is not None else ""

        #: pathlib.Path: Path to a textfile, if specified in the init
        self.path: Path = Path(path) if path is not None else path

        #: bool: Boolean flag, indicating whether emoji shortcodes should be
        #: interpreted
        self.emojize: bool = emojize
        self.render_markdown: bool = render_markdown

        if self._text and self.path:
            raise ValueError("You can only specify one of 'text' and 'path'.")

    @property
    def text(self) -> str:
        """str: The text to be displayed"""
        if self.path:
            return self.experiment.subpath(self.path).read_text()
        else:
            return self._text

    def render_text(self) -> str:
        """
        Renders the markdown and emoji shortcodes in :attr:`.text`

        Returns:
            str: Text rendered to html code
        """

        text = self.text

        if self.emojize:
            text = emojize(text, use_aliases=True)
        if self.render_markdown:
            text = cmarkgfm.github_flavored_markdown_to_html(text, options=cmarkgfmOptions.CMARK_OPT_UNSAFE)
        return text

    @text.setter
    def text(self, text):
        self._text = text

    @property
    def element_width(self) -> str:
        
        if self.width is not None:
            return " ".join(self.converted_width)

        responsive = self.experiment.config.getboolean("layout", "responsive", fallback=True)
        if responsive:
            if self._element_width is None:
                return " ".join(["col-12", "col-sm-11", "col-lg-10", "col-xl-9"])
            else:
                return " ".join(self._element_width)
        elif not responsive:
            return "col-9"

    @property
    def template_data(self) -> dict:
        
        d = super().template_data
        d["text"] = self.render_text()

        return d

@inherit_kwargs
class Image(Element):
    """
    Displays an image.

    Args:
        path: Path to the image. Can be relative to the experiment
            directory, or absolute.
        url: URL to the image.
        {kwargs}

    Notes:
        You can specify *either* a path, or a url, but not both.

    Examples:
        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo1"

                def on_exp_access(self):
                    pylogo = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Python_logo_and_wordmark.svg/1920px-Python_logo_and_wordmark.svg.png"

                    self += al.Image(url=pylogo)

    """

    # Documented at :class:`.Element`
    element_template = jinja_env.get_template("html/ImageElement.html.j2")

    def __init__(self, path: Union[str, Path] = None, url: str = None, **kwargs):
        super().__init__(**kwargs)

        self.path = path
        if url is not None and not is_url(url):
            raise ValueError("Supplied value is not a valid url.")
        else:
            self.url = url

        if path and url:
            raise ValueError("You can only specify one of 'path' and 'url'.")

        self.src = None

    def added_to_experiment(self, experiment):
        """
        The image is added to the dict of static files, if a path is
        provided.

        :meta private: (documented at :class:`.Element`)
        """
        super().added_to_experiment(experiment)
        if self.path:
            p = self.experiment.subpath(self.path)
            url = self.experiment.ui.add_static_file(p)
            self.src = url
        else:
            self.src = self.url

    @property
    def template_data(self):
        
        d = super().template_data
        d["src"] = self.src
        return d

@inherit_kwargs
class Audio(Image):
    """
    Allows playing audio files.

    Args:
        path: Path to the audio file. Can be relative to the experiment
            directory, or absolute.
        url: URL to the audio file.
        controls: If *True*, alfred will display controls like a pause/
            play button for participants to use (default: *True*).
        autoplay: If *True*, the audio file will start to play
            automatically (default: *False*).
        loop: If *True*, the audio file will start playing from the
            beginning again, once the end is reached (default: *False*).
        {kwargs}

    Notes:
        You can specify *either* a path, or a url, but not both.

    Examples:
        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo1"

                def on_exp_access(self):
                    demo_audio = "https://file-examples-com.github.io/uploads/2017/11/file_example_MP3_1MG.mp3"

                    self += al.Audio(url=demo_audio)

    """

    # Documented at :class:`.Element`
    element_template = jinja_env.get_template("html/AudioElement.html.j2")

    def __init__(
        self,
        path: Union[str, Path] = None,
        url: str = None,
        controls: bool = True,
        autoplay: bool = False,
        loop: bool = False,
        align: str = "center",
        **kwargs,
    ):
        super().__init__(path=path, url=url, align=align, **kwargs)
        self.controls = controls
        self.autoplay = autoplay
        self.loop = loop

    @property
    def template_data(self):
        
        d = super().template_data
        d["controls"] = self.controls
        d["autoplay"] = self.autoplay
        d["loop"] = self.loop

        return d

@inherit_kwargs
class Video(Audio):
    """
    Displays a video on the page.

    Args:
        path: Path to the video (relative to the experiment)
        url: Url to the video
        allow_fullscreen: Boolean, indicating whether users can enable
            fullscreen mode.
        video_height: Video height in absolute pixels (without unit).
            Defaults to "auto".
        video_width: Video width in absolute pixels (without unit).
            Defaults to "100%". It is recommended to use leave this
            parameter at the default value and use the general element
            parameter *width* for setting the width.
        {kwargs}

    Notes:
        You can specify *either* a path, or a url, but not both.

    Examples:
        Minimal example::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo1"

                def on_exp_access(self):
                    demo_video = "https://file-examples-com.github.io/uploads/2017/04/file_example_MP4_480_1_5MG.mp4"

                    self += al.Video(url=demo_video)

    """

    # Documented at :class:`.Element`
    element_template = jinja_env.get_template("html/VideoElement.html.j2")

    def __init__(
        self,
        path: Union[str, Path] = None,
        url: str = None,
        allow_fullscreen: bool = True,
        video_height: str = "auto",
        video_width: str = "100%",
        **kwargs,
    ):
        super().__init__(path=path, url=url, **kwargs)
        self.video_height = video_height
        self.video_width = video_width
        self.allow_fullscreen = allow_fullscreen

    @property
    def template_data(self):
        
        d = super().template_data
        d["video_height"] = self.video_height
        d["video_width"] = self.video_width
        d["allow_fullscreen"] = self.allow_fullscreen

        return d

@inherit_kwargs
class MatPlot(Element):
    """
    Displays a :class:`matplotlib.figure.Figure` object.

    Args:
        fig (matplotlib.figure.Figure): The figure to display.
        {kwargs}

    Notes:
        When plotting in alfred, you need to use the Object-oriented
        matplotlib API
        (https://matplotlib.org/3.3.3/api/index.html#the-object-oriented-api).

    Examples:
        Minimal example::

            from matplotlib.figure import Figure
            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo1"

                def on_exp_access(self):

                    # build an example plot
                    fig = Figure()
                    ax = fig.add_subplot()
                    ax.plot(range(10))

                    # add plot to page
                    self += al.MatPlot(fig=fig)

    """

    # Documented at :class:`.Element`
    element_template = jinja_env.get_template("html/ImageElement.html.j2")

    def __init__(self, fig, align: str = "center", **kwargs):
        super().__init__(align=align, **kwargs)
        self.fig = fig
        self.src = None

    def prepare_web_widget(self):
        
        out = io.BytesIO()
        self.fig.savefig(out, format="svg")
        out.seek(0)
        self.src = self.exp.ui.add_dynamic_file(out, content_type="image/svg+xml")

    @property
    def template_data(self):
        
        d = super().template_data
        d["src"] = self.src
        return d


class Hline(Element):
    """
    A simple horizontal line.
    
    Examples:
        Two text elements, separated by a horizontal line::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.Text(text="Text 1")
                    self += al.Hline()
                    self += al.Text(text="Text 2")
              
    """

    def __init__(self):
        super().__init__()

    def render_inner_html(self, template_data: dict) -> str:
        """
        A redefined render_inner_html method still needs to accept the
        *template_data* argument, even if it does not use it.

        :meta private: (documented at :class:`.Element`)
        """
        return "<hr>"

@inherit_kwargs
class CodeBlock(Text):
    """
    A convenience element for displaying highlighted code.

    Args:
        text: The code to be displayed.
        path: path: Filepath to a textfile (relative to the experiment
            directory) from which to read code.
        lang: The programming language to highlight. Defaults
            to 'auto', which tries to auto-detect the right language.
            See https://prismjs.com/index.html#supported-languages
            for an overview of possible language codes. Note that
            we may currently not support all possible languages.
        {kwargs}

    Examples:
        ::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):
                    self += al.CodeBlock(text="console.log('test');", lang="javascript")

    """

    def __init__(
        self,
        text: str = None,
        path: Union[Path, str] = None,
        lang: str = "auto",
        width: str = "full",
        **element_args,
    ):

        """Constructor method."""
        super().__init__(text=text, path=path, width=width, **element_args)
        self.lang = lang if lang is not None else ""

    @property
    def text(self):
        
        if self.path:
            text = self.experiment.subpath(self.path).read_text()

            code = f"```{self.lang}\n{text}\n```"
            return code
        else:
            code = f"```{self.lang}\n{self._text}\n```"
            return code

@inherit_kwargs
class Label(Text):
    """
    A utility class, serving as label for other elements.
    
    Args:
        text: Text to be displayed.
        width: Usage as in :class:`.Element`, with the same default ('full').
        {kwargs}

    """

    def __init__(self, text, width="full", **kwargs):
        super().__init__(text=text, width=width, **kwargs)

        #: RowLayout: Layouting facility for controlling the column
        #: breaks and vertical alignment of the label. Gets set by
        #: :class:`.LabelledElement` automatically.
        self.layout: RowLayout = None

        #: Tells the label which column of the :attr:`.layout` it is
        self.layout_col: int = None

    @property
    def col_breaks(self) -> str:
        """The label's breakpoints for diferent screen sizes."""
        return self.layout.col_breaks(self.layout_col)

    @property
    def vertical_alignment(self) -> str:
        """The label's vertical alignment"""
        return self.layout.valign_cols[self.layout_col]

@inherit_kwargs
class ProgressBar(LabelledElement):
    """
    Displays a progress bar.

    Args:
        progress: Can be either "auto", or a number between 0 and 100.
            If "auto", the progress is calculated from the current
            progress of the experiment. If a number is supplied, that
            number will be used as the progress to be displayed.
        bar_height: Height of the progress bar. Supply a string with
            unit, e.g. "6px".
        show text: Indicates, whether the progress bar should include
            text with the current progress.
        striped: Indicates, whether the progress bar shoulb be striped.
        style: Determines the color of the progress bar. Possible values
            are "primary", "secondary", "info", "success", "warning",
            "danger", "light", "dark".
        animated: Determines, whether a striped progress bar should be
            equipped with an animation.
        round: Determines, whether the corners of the progress bar
            should be round.
        {kwargs}

    See Also:
        See :attr:`.ExperimentSession.progress_bar` for more information
        on the experiment-wide progress bar.

    Notes:
        If the argument *show_text* is *True*, the text's appearance
        can be altered via CSS. It receives a class of
        ":attr:`.css_class_element`-text" and an id of
        ":attr:`.Element.name`-text". You can use the method :meth:`.add_css`
        to append fitting CSS to the bar (see examples).

    Examples:

        Overriding the default experiment-wide progress bar::

            import alfred3 as al
            exp = al.Experiment()

            @exp.setup
            def setup(exp_session):
                exp_session.progress_bar = al.ProgressBar(show_text=True, bar_height="15px")

            exp += al.Page(name="example_page")

        Adding a progress bar as an element to a page::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Example(al.Page):
                name = "example_page"

                def on_exp_access(self):
                    self += al.ProgressBar()

        Altering the progress bar text's apperance, applied to the
        experiment-wide progress bar. Note that the experiment-wide
        progress bar *always* receives the name "*progress_bar_*"::

            import alfred3 as al
            exp = al.Experiment()

            @exp.setup
            def setup(exp):
                exp.progress_bar = al.ProgressBar(show_text=True, bar_height="15px")
                exp.progress_bar.add_css("#progress_bar_ {{font-size: 12pt;}}")

            exp += al.Page(name="example_page")

    """

    element_template = jinja_env.get_template("html/ProgressBarElement.html.j2")

    def __init__(
        self,
        progress: Union[str, float, int] = "auto",
        bar_height: str = "6px",
        show_text: bool = False,
        striped: bool = True,
        style: str = "primary",
        animated: bool = False,
        round_corners: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._progress_setting = progress

        if not isinstance(progress, (str, float, int)):
            raise TypeError

        self._progress: int = None
        self._bar_height: str = bar_height
        self._show_text: bool = show_text
        self._striped: bool = striped
        self._bar_style: str = style
        self._animated: bool = animated
        self._round_corners: bool = "border-radius: 0;" if round_corners == False else ""

    def added_to_experiment(self, exp):
        
        super().added_to_experiment(exp)

        css = f".progress#{self.name}  {{height: {self._bar_height}; {self._round_corners}}}"
        self.add_css(code=css)

    def _prepare_web_widget(self):
        if self._progress_setting == "auto":
            self._progress = self._calculate_progress()
        elif isinstance(self._progress_setting, (int, float)):
            self._progress = self._progress_setting

        self.prepare_web_widget()

        try:
            self._activate_showif_on_current_page()
        except AttributeError as e:
            # special treatment for experiment-wide progress bar
            # because that one only has an experiment, no page
            if self.page is None and self.name == "progress_bar_":
                pass
            else:
                raise e

    def _calculate_progress(self) -> float:
        """
        Calculates the current progress.

        Returns:
            float: Current progress
        """
        n_el = 0
        for el in self.exp.root_section.all_input_elements.values():
            if el.should_be_shown:
                n_el += 1
            elif el.showif or el.page.showif or el.section.showif:
                n_el += 0.3

        n_pg = len(self.experiment.root_section.visible("all_pages"))
        shown_el = len(self.experiment.root_section.all_shown_input_elements)
        shown_pg = len(self.experiment.root_section.all_shown_pages)
        exact_progress = ((shown_el + shown_pg) / (n_el + n_pg)) * 100

        if not self.experiment.finished and not self.experiment.aborted:
            return min(round(exact_progress, 1), 95)
        else:
            return 100

    @property
    def template_data(self):
        
        d = super().template_data
        d["progress"] = self._progress
        d["show_text"] = self._show_text
        d["bar_height"] = self._bar_height
        d["bar_style"] = f"bg-{self._bar_style}"
        d["striped"] = "progress-bar-striped" if self._striped else ""
        d["animated"] = "progress-bar-animated" if self._animated else ""
        return d


class Alert(Text):
    """
    Allows the display of customized alerts.

    Args:
        text: Alert text
        category: Affects the appearance of alerts.
            Values can be: "info", "success", "warning", "primary",
            "secondory", "dark", "light", "danger".
        dismiss: Boolean parameter. If "True", AlertElement can be
            dismissed by a click. If "False", AlertElement is not
            dismissible. Default = "False"
        **element_args: Keyword arguments passed to the parent class
            :class:`TextElement`. Accepted keyword arguments are: name,
            font_size, align, width, position, showif,
            instance_log.

    Examples:

        >>> import alfred3 as al
        >>> alert = al.AlertElement(text="Alert text", dismiss=True, name="al1")
        >>> alert
        Alert(name='al1')

    """

    element_template = jinja_env.get_template("html/AlertElement.html.j2")

    def __init__(
        self, text: str = "", category: str = "info", dismiss: bool = False, **element_args
    ):
        super().__init__(text=text, **element_args)
        self.category = category
        self.dismiss = dismiss

    @property
    def template_data(self):
        d = super().template_data
        d["category"] = self.category
        d["role"] = "alert"
        d["dismiss"] = self.dismiss

        return d


class ButtonLabels(SingleChoiceButtons):
    """
    Disabled buttons to use for labelling.

    Args:
        *choice_labels: Variable numbers of choice labels. See
            :class:`.ChoiceElement` for details.
        {kwargs}

    Examples:
        Using button labels to label single choice buttons::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):

                    self += al.ButtonLabels("label1", "label2")
                    self += al.SingleChoiceButtons("choice1", "choice2", name="b1")

    """

    def __init__(self, *choice_labels, **kwargs):
        name = f"{type(self).__name__}" + uuid4().hex
        super().__init__(*choice_labels, disabled=True, name=name, **kwargs)

    @property
    def data(self):
        
        return {}

@inherit_kwargs
class BarLabels(ButtonLabels):
    """
    Disabled button bar to use for labelling.

    Args:
        *choice_labels: Variable numbers of choice labels. See
            :class:`.ChoiceElement` for details.
        {kwargs}

    Examples:
        Using button labels to label single choice buttons::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                name = "demo"

                def on_exp_access(self):

                    self += al.BarLabels("label1", "label2")
                    self += al.SingleChoiceBar("choice1", "choice2", name="b1")

    """

    # Documented at :class:`.SingleChoiceButtons`
    button_group_class = "choice-button-bar"

    # Documented at :class:`.SingleChoiceButtons`
    button_toolbar = True

@inherit_kwargs
class CountUp(Element):
    """
    Displays a timer, counting up from 00:00:00 (hh:mm:ss).

    Args:
        end_after (int): Optional argument for specifying an end for 
            the counter after a number of seconds. Defaults to *-1*, which
            will let the counter run indefinitely.
        end_msg (str): Text to be displayed in the counter's place upon
            expiration.
        {kwargs}
    
    Examples:
        
        ::

            import alfred3 as al
            exp = al.Experiment()
            
            @exp.member
            class Demo(al.Page):
                def on_exp_access(self):
                    self += al.CountUp(font_size="big", align="center")

    """

    counter_js = jinja_env.get_template("js/countup.js.j2")
    element_template = jinja_env.get_template("html/TextElement.html.j2")

    def __init__(self, end_after: int = -1, end_msg: str = "expired", **kwargs):
        super().__init__(**kwargs)

        self.end_after = end_after
        self.end_msg = end_msg
        
    
    def prepare_web_widget(self):
        self._js_code = []
        js = self.counter_js.render(name=self.name, end_after=self.end_after, end_msg=self.end_msg)
        self.add_js(js)


@inherit_kwargs
class CountDown(CountUp):
    """
    Displays a countdown, counting down from now (time of page loading)
    to a specified end.

    Args:
        end_after (int): The amount of seconds after which the countdown
            ends. Alternatively, you can specifiy a specific time with
            the alternative constructor :meth:`.tilldate`.
        end_msg (str): Text to be displayed in the countdown's place upon
            expiration.
        {kwargs}
    
    Examples:
        Countdown running 30 seconds::
            
            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                def on_exp_access(self):
                    self += al.CounDown(end_after=30, font_size="big", align="center")
        
        Countdown running until a certain datetime is reached::

            import alfred3 as al
            exp = al.Experiment()

            @exp.member
            class Demo(al.Page):
                def on_exp_access(self):
                    self += al.CounDown.tilldate(
                        year=2031, 
                        month=1, 
                        day=31, 
                        hour=12, 
                        minute=30, 
                        second=12, 
                        font_size="big", 
                        align="center"
                        )
    """
    counter_js = jinja_env.get_template("js/countdown.js.j2")
    element_template = jinja_env.get_template("html/TextElement.html.j2")

    def __init__(self, end_after: int, end_msg: str = "expired", **kwargs):
        super().__init__(**kwargs)

        self.end_after = end_after
        self.end_msg = end_msg
    

    @classmethod
    def tilldate(cls, year: int = None, month: int = None, day: int = None, hour: int = None, minute: int = None, second: int = None, **kwargs):
        """
        Alternative constructor for a countdown targeted at a specific date.

        Args:
            year, month, day, hour, minute, second: Time units, all 
                integers. Cannot have leading zeroes. It is fine to 
                specific only, for example, the year and the month. The
                arguments will be passed on to :class:`datetime.datetime`
                to construct a time object.
            
            **kwargs: Further keyword arguments are passed on to the
                ordinary constructor, see :class:`.CountDown`.
        
        Examples:

            Countdown running until a certain datetime is reached::

                import alfred3 as al
                exp = al.Experiment()

                @exp.member
                class Demo(al.Page):
                    def on_exp_access(self):
                        self += al.CounDown.tilldate(
                            year=2031, 
                            month=1, 
                            day=31, 
                            hour=12, 
                            minute=30, 
                            second=12, 
                            font_size="big", 
                            align="center"
                            )
        """
        if "end_after" in kwargs:
            raise TypeError("'end_after' is an invalid keyword argument for the 'fromdate' constructor.")
        
        dargs = {}
        if year:
            dargs["year"] = year
        if month:
            dargs["month"] = month
        if day:
            dargs["day"] = day
        if hour:
            dargs["hour"] = hour
        if minute:
            dargs["minute"] = minute
        if second:
            dargs["second"] = second
        
        date = datetime(**dargs)
        now = datetime.now()
        diff = date - now

        return cls(end_after=diff.total_seconds(), **kwargs)

