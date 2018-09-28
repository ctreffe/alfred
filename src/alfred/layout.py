# -*- coding:utf-8 -*-

'''
.. moduleauthor:: Paul Wiemann <paulwiemann@gmail.com>

.. todo:: Beim Modulimport wird ein Fehler angezeigt. Gibt es wirklich eine Klasse *Template* in **jinja2**?
'''


import os.path
from abc import ABCMeta, abstractmethod, abstractproperty
from jinja2 import Template, Environment, PackageLoader

from PySide.QtGui import QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QComboBox, QPixmap, QSizePolicy, QLayout
from PySide.QtUiTools import QUiLoader
from PySide.QtCore import QFile, Slot, Qt, QSize
import alfred.settings as settings


from _core import package_path

jinja_env = Environment(loader=PackageLoader('alfred', 'templates'))

class Layout(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self._experiment = None
        self._uiController = None
        self._backwardText = u"Zurück"
        self._forwardText = u"Weiter"
        self._finishText = u"Beenden"
        self._backwardEnabled = True
        self._forwardEnabled = True
        self._finishedDisabled = False
        self._jumpListEnabled = True
        self._jumpList = []

    def activate(self, experiment, uiController):
        self._experiment = experiment
        self._uiController = uiController
        
    def deactivate(self):
        self._experiment = None
        self._uiController = None

    @abstractmethod
    def render(self, widget):
        pass

    @property
    def backwardEnabled(self):
        return self._backwardEnabled
    @backwardEnabled.setter
    def backwardEnabled(self, b):
        self._backwardEnabled = b

    @property
    def forwardEnabled(self):
        return self._forwardEnabled
    @forwardEnabled.setter
    def forwardEnabled(self, b):
        self._forwardEnabled = b

    @property
    def finishDisabled(self):
        return self._finishedDisabled

    @finishDisabled.setter
    def finishDisabled(self, b):
        self._finishedDisabled = b

    @property
    def backwardText(self):
        return self._backwardText
    @backwardText.setter
    def backwardText(self, text):
        self._backwardText = text

    @property
    def forwardText(self):
        return self._forwardText
    @forwardText.setter
    def forwardText(self, text):
        self._forwardText = text

    @property
    def finishText(self):
        return self._finishText
    @finishText.setter
    def finishText(self, text):
        self._finishText = text

    @property
    def jumpListEnabled(self):
        return self._jumpListEnabled
    @jumpListEnabled.setter
    def jumpListEnabled(self, b):
        self._jumpListEnabled = b
        
    
class BaseWebLayout(Layout):

    def __init__(self):
        super(BaseWebLayout, self).__init__()
        self._style_urls = []
        self._js_urls = []
        self._template = jinja_env.get_template('base_layout.html')

    def activate(self, experiment, uiController):
        super(BaseWebLayout, self).activate(experiment, uiController)
        # add css files
        self._style_urls.append((99,self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/base_web_layout.css'), content_type="text/css")))
        self._style_urls.append((1,self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/bootstrap.min.css'), content_type="text/css")))
        self._style_urls.append((2,self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/jquery-ui.css'), content_type="text/css")))
        #self._style_urls.append(self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/app.css'), content_type="text/css"))

        # add js files
        self._js_urls.append((01,
            self._uiController.addStaticFile(
                os.path.join(package_path(), 'static/js/jquery-1.8.3.min.js'),
                content_type="text/javascript")
            ))
        self._js_urls.append((02,self._uiController.addStaticFile(os.path.join(package_path(), 'static/js/bootstrap.min.js'), content_type="text/javascript")))
        self._js_urls.append((03,self._uiController.addStaticFile(os.path.join(package_path(), 'static/js/jquery-ui.js'), content_type="text/javascript")))

        self._js_urls.append((10,
            self._uiController.addStaticFile(
                os.path.join(package_path(), 'static/js/baseweblayout.js'),
                content_type="text/javascript")
            ))

        self._logo_url = self._uiController.addStaticFile(os.path.join(package_path(), 'static/img/alfred_logo.png'), content_type="image/png")

    @property
    def cssCode(self):
        return []

    @property
    def cssURLs(self):
        return self._style_urls

    @property
    def javascriptCode(self):
        return []

    @property
    def javascriptURLs(self):
        return self._js_urls

    def render(self):

        d = {}
        d['logo_url'] = self._logo_url
        d['widget'] = self._experiment.questionController.currentQuestion.webWidget

        if self._experiment.questionController.currentTitle:
            d['title'] = self._experiment.questionController.currentTitle

        if self._experiment.questionController.currentSubtitle:
            d['subtitle'] = self._experiment.questionController.currentSubtitle

        if self._experiment.questionController.currentStatustext:
            d['statustext'] = self._experiment.questionController.currentStatustext

        if not self._experiment.questionController.currentQuestion.canDisplayCorrectiveHintsInline \
                and self._experiment.questionController.currentQuestion.correctiveHints:
            d['corrective_hints'] = self._experiment.questionController.currentQuestion.correctiveHints

        if self.backwardEnabled and self._experiment.questionController.canMoveBackward:
            d['backward_text'] = self.backwardText

        if self.forwardEnabled:
            if self._experiment.questionController.canMoveForward:
                d['forward_text'] = self.forwardText
            else:
                if not self._finishedDisabled:
                    d['finish_text'] = self.finishText

        if self.jumpListEnabled and self._experiment.questionController.jumplist:
            jmplist = self._experiment.questionController.jumplist 
            for i in range(len(jmplist)):
                jmplist[i] = list(jmplist[i])
                jmplist[i][0] = '.'.join(map(str, jmplist[i][0]))
            d['jumpList'] = jmplist

        messages = self._experiment.messageManager.getMessages()
        if messages:
            for message in messages:
                message.level = '' if message.level == 'warning' else 'alert-' + message.level # level to bootstrap
            d['messages'] = messages


        return self._template.render(d)


    @property
    def backwardLink(self):
        return self._backwardLink
    @backwardLink.setter
    def backwardLink(self, link):
        self._backwardLink = link

    @property
    def forwardLink(self):
        return self._forwardLink
    @forwardLink.setter
    def forwardLink(self, link):
        self._forwardLink = link


class BaseQtLayout(Layout):
    def __init__(self):
        super(BaseQtLayout, self).__init__()

        self._oldQuestion = None
        
        self._maximum_width = 1007
        self._minimum_height = 700
        
        self._maximumWidgetWidth = self._maximum_width-40
        
        layout_margin = 0
        if settings.experiment.qtFullScreen:
            layout_margin = 30
            
        #########################################################################
        
        # Main Widget
        
        #########################################################################
        
        self._qtBaseWidget = QWidget()
        self._qtBaseWidget.setObjectName('BaseWidget')
        self._qtBaseWidget.setStyleSheet('QWidget#BaseWidget {background:white;}')
        self._qtBaseWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        
        self._qtOuterWidget = QWidget()
        self._qtOuterWidget.setStyleSheet('QWidget#BaseWidget {background:green;}')
        self._qtOuterWidget.setMinimumSize(self._maximum_width,self._minimum_height) #Needs 1px margin + 16px for ScrollBar to minimum window size
        self._qtOuterWidget.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum) # horizontal, vertical
        
        self._qtBaseLayout = QVBoxLayout()
        self._qtBaseLayout.setContentsMargins(0,layout_margin,0,layout_margin) #left,top,right,bottom
        self._qtBaseLayout.addWidget(self._qtOuterWidget)
        self._qtBaseLayout.setAlignment(self._qtOuterWidget, Qt.AlignHCenter | Qt.AlignTop)
        
        self._qtBaseWidget.setLayout(self._qtBaseLayout)
        
        self._qtOuterLayout = QVBoxLayout()
        self._qtOuterLayout.setContentsMargins(0,0,0,0) #left,top,right,bottom
        self._qtOuterLayout.setSpacing(0)
    
        self._qtOuterWidget.setLayout(self._qtOuterLayout)
    
        #########################################################################
        
        # Header
        
        #########################################################################
        
        self._header = QWidget()
        self._header.setStyleSheet('background:#C0C0C0;')
        self._header.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        
        self._headerTitle = QLabel()
        self._headerTitle.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self._headerSubTitle = QLabel()
        self._headerSubTitle.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self._headLogo = QLabel()
        
        self._headerTitle.setText(u'')
        self._headerTitle.setStyleSheet('padding-left: 15px; color:#FFFFFF; font-family: Arial,Helvetica,sans-serif; font-size: 24pt;')

        self._headerSubTitle.setText(u'')
        self._headerSubTitle.setStyleSheet('padding-left: 20px; color:#999999; font-family: Arial,Helvetica,sans-serif; font-size: 16pt;')
        
        self._headLogo.setPixmap(QPixmap(os.path.join(package_path(), 'static/img/alfred_logo.png')))
        self._headLogo.setStyleSheet('padding: 5px; padding-bottom: 10px;')
        self._headLogo.setScaledContents(True)
        self._headLogo.setFixedHeight(130)
        self._headLogo.setFixedWidth(280)
        
        self._headerTitleLayout = QVBoxLayout()
        self._headerTitleLayout.setContentsMargins(0,0,0,0) # left,top,right,bottom
        self._headerTitleLayout.setSpacing(0)
        self._headerTitleLayout.addWidget(self._headerTitle)
        self._headerTitleLayout.addWidget(self._headerSubTitle)
 
        self._headerLayout = QHBoxLayout()
        self._headerLayout.setContentsMargins(0,0,0,0) # left,top,right,bottom
        self._headerLayout.setSpacing(0)
        self._headerLayout.addWidget(self._headLogo)
        self._headerLayout.addLayout(self._headerTitleLayout)

       
        self._header.setLayout(self._headerLayout)
       
        self._qtOuterLayout.addWidget(self._header)
        
        
        #########################################################################
        
        # Content frame
        
        #########################################################################
        
        
        self._contentFrame = QWidget()
        
        self._contentFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        
        content_palette = self._contentFrame.palette()
        content_palette.setColor(self._contentFrame.backgroundRole(), 'whiteSmoke')
        self._contentFrame.setPalette(content_palette)
        self._contentFrame.setAutoFillBackground(True)
        
        self._messageLayout = QVBoxLayout()
        self._messageLayout.setContentsMargins(0,0,0,0) # left,top,right,bottom
        self._messageLayout.setSpacing(3)
        
        self._title = QLabel('Default-Title')
        self._title.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        self._title.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: 18pt;')
        
        self._subTitle = QLabel('Default-Subtitle')
        self._subTitle.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        self._subTitle.setStyleSheet('color: darkGrey; font-family: Arial,Helvetica,sans-serif; font-size: 14pt;')
        
        self._correctiveHints = QLabel('Default-CorrectiveHints')
        self._correctiveHints.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        self._correctiveHints.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: 12pt;')
        
        self._containerLayout = QVBoxLayout()
        self._containerLayout.setContentsMargins(0,0,0,0) # left,top,right,bottom
        self._containerLayout.setSpacing(0)
        
        self._status = QLabel('Default-Status')
        self._status.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        self._status.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: 9pt; padding-top: 5px;')
        
        self._contentFrameLayout = QVBoxLayout()
        self._contentFrameLayout.setSizeConstraint(QLayout.SetFixedSize)
        self._contentFrameLayout.setContentsMargins(20,10,20,3) # left,top,right,bottom
        self._contentFrameLayout.setSpacing(5)
        self._contentFrameLayout.addLayout(self._messageLayout)
        self._contentFrameLayout.addWidget(self._title)
        self._contentFrameLayout.addWidget(self._subTitle)
        self._contentFrameLayout.addWidget(self._correctiveHints)
        self._contentFrameLayout.addLayout(self._containerLayout)
        self._contentFrameLayout.addStretch()
        self._contentFrameLayout.addWidget(self._status)
        
        self._contentFrame.setLayout(self._contentFrameLayout)
       
        self._qtOuterLayout.addWidget(self._contentFrame)
        

        #########################################################################
        
        # ControlBar
        
        #########################################################################
        
        
        self._controlBar = QWidget()
        self._controlBar.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        
        # Palette based Approach to change background color

        control_palette = self._controlBar.palette()
        control_palette.setColor(self._controlBar.backgroundRole(), '#8f8f91')
        self._controlBar.setPalette(control_palette)
        self._controlBar.setAutoFillBackground(True)
        
        self._forwardButton = QPushButton('Default-Forward')
        self._forwardButton.setMinimumSize(50,30)
        self._forwardButton.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Fixed)
        self._forwardButton.setStyleSheet('QPushButton {font-family: Arial,Helvetica,sans-serif; font-size: 11pt;text-align: center;padding: 2px;border: 1px outset #8f8f91;border-radius: 6px;background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #f6f7fa, stop: 1 #dadbde);min-width: 80px;} QPushButton:pressed {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #dadbde, stop: 1 #f6f7fa);}')


        self._backwardButton = QPushButton('Default-Backward')
        self._backwardButton.setMinimumSize(50,30)
        self._backwardButton.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Fixed)
        self._backwardButton.setStyleSheet('QPushButton {font-family: Arial,Helvetica,sans-serif; font-size: 11pt;text-align: center;padding: 2px;border: 1px outset #8f8f91;border-radius: 6px;background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #f6f7fa, stop: 1 #dadbde);min-width: 80px;} QPushButton:pressed {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #dadbde, stop: 1 #f6f7fa);}')
        
        self._jumpBox = QComboBox()
        self._jumpBox.setMinimumSize(80,30)
        self._jumpBox.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Fixed)
        self._jumpBox.setStyleSheet('QComboBox {font-family: Arial,Helvetica,sans-serif; font-size: 11pt;text-align: center;padding: 2px;border: 1px outset #8f8f91;border-radius: 6px;background-color: white; min-width: 80px;} QComboBox:drop-down {height: 20px; top: 4px; right: 3px;} QComboBox QAbstractItemView {padding: 2px; border: 1px solid #8f8f91; border-radius:6px; background-color: white;}')
        self._jumpBox.addItem('Default-Select')
        
        self._controlBarLayout = QHBoxLayout()
        self._controlBarLayout.setContentsMargins(0,4,0,4) # left,top,right,bottom
        self._controlBarLayout.setSpacing(5)
     
        self._controlBarLayout.addStretch()
        self._controlBarLayout.addWidget(self._backwardButton)
        self._controlBarLayout.addWidget(self._jumpBox)
        self._controlBarLayout.addWidget(self._forwardButton)
        self._controlBarLayout.addStretch()


        self._controlBar.setLayout(self._controlBarLayout)
   
        self._qtOuterLayout.addWidget(self._controlBar)
        
        
        #########################################################################
        
        # Footer
        
        #########################################################################
        
        self._footerBar = QWidget()
        self._footerBar.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        self._footerBar.setStyleSheet('background:#C0C0C0;')
        
        footer = QLabel('Alfredo Web Experiment')
        footer.setAlignment(Qt.AlignHCenter)
        footer.setStyleSheet('padding: 3px; color: black; font-family: Arial,Helvetica,sans-serif; font-size: 10pt;')
        
        self._footerBarLayout = QHBoxLayout()
        self._footerBarLayout.setContentsMargins(0,0,0,0) # left,top,right,bottom
        self._footerBarLayout.setSpacing(0)
        self._footerBarLayout.addWidget(footer)
        
        self._footerBar.setLayout(self._footerBarLayout)
        
        self._qtOuterLayout.addWidget(self._footerBar)
        
        #########################################################################
        
        # Connects between signals and slots
        
        #########################################################################

        self._forwardButton.clicked.connect(self.forwardClick)
        self._backwardButton.clicked.connect(self.backwardClick)
        self._jumpBox.activated.connect(self.jumpActivated)
        
        
    def render(self):
        if self._oldQuestion is not None:
            oldQtWidget = self._oldQuestion.qtWidget
            self._containerLayout.removeWidget(oldQtWidget)
            oldQtWidget.hide()
            oldQtWidget.setParent(None)
            self._oldQuestion = None

        if self._experiment.questionController.currentTitle:
            self._title.show()
            self._title.setText(self._experiment.questionController.currentTitle)
        else:
            self._title.hide()

        if self._experiment.questionController.currentSubtitle:
            self._subTitle.show()
            self._subTitle.setText(self._experiment.questionController.currentSubtitle)
        else:
            self._subTitle.hide()

        if self._experiment.questionController.currentStatustext:
            self._status.show()
            self._status.setText(self._experiment.questionController.currentStatustext)
        else:
            self._status.hide()

        if not self._experiment.questionController.currentQuestion.canDisplayCorrectiveHintsInline \
                and self._experiment.questionController.currentQuestion.correctiveHints:
            self._correctiveHints.show()
            self._correctiveHints.setText(self._experiment.questionController.currentQuestion.correctiveHints)
        else:
            self._correctiveHints.hide()

        if self.backwardEnabled and self._experiment.questionController.canMoveBackward:
            self._backwardButton.setVisible(True)
            self._backwardButton.setText(self._backwardText)
        else:
            self._backwardButton.setText(self._backwardText)
            self._backwardButton.setVisible(False)

        if self.forwardEnabled and self._experiment.questionController.canMoveForward:
            self._forwardButton.setText(self._forwardText)
            self._forwardButton.setVisible(True)
            
        elif self.forwardEnabled and not (self._experiment.questionController.canMoveForward or self._finishedDisabled):
            self._forwardButton.setText(self._finishText)
            self._forwardButton.setVisible(True)
            
        else:
            self._forwardButton.setText(self._forwardText)
            self._forwardButton.setVisible(False)

        if self.jumpListEnabled and self._experiment.questionController.jumplist: 
            self._jumpList = self._experiment.questionController.jumplist
            self._jumpBox.setVisible(True)
            self._jumpList = [([-1],u'Bitte wählen')] + self._jumpList #Dieser Eintrag erscheint immer ganz oben und wird beim jumpen übersprungen
            self._jumpBox.clear()
            for item in self._jumpList:
                self._jumpBox.addItem(item[1])
        else:
            self._jumpBox.setVisible(False)
        
        # Deleting old Messages
        
        widgetSet = True

        #Hier das Layout leeren!
        while widgetSet:
            widget = self._messageLayout.takeAt(0)
            if widget == None:
                widgetSet = False
            else:
                widget.widget().setParent(None)
        
        # Adding Messages
            
        messages = self._experiment.messageManager.getMessages()
        
        for message in messages:
            output = ''
            
            if not message.title == '':
                output = output + '<strong>' + message.title + '</strong> - '
            
            output = output + message.msg
            
            message_element = QLabel(output)
                
            if message.level == 'warning':
                bg_color = '#FCF8E3'
                text_color = '#C09853'
                
            elif message.level == 'error':
                bg_color = '#F2DEDE'
                text_color = '#B94A48'
                
            elif message.level == 'info':
                bg_color = '#D9EDF7'
                text_color = '#3A87AD'
            
            elif message.level == 'success':
                bg_color = '#DFF0D8'
                text_color = '#468847'
                
            # Warning Background: #FCF8E3 / Warning Color: #C09853
            # Error Background: #F2DEDE / Error Color: #B94A48
            # Info Background: #D9EDF7 / Info Color: #3A87AD
            # Success Background: #DFF0D8 / Success Color: #468847
            
            message_element.setStyleSheet('font-family: Arial,Helvetica,sans-serif; font-size: 12pt; background-color: '+bg_color+'; color: '+text_color+'; padding: 3px; border-width: 1px; border-style: solid; border-radius: 4px; border-color: '+text_color+';')
            
            self._messageLayout.addWidget(message_element)

        # Hier wird das innere Fragen-Widget geadded!!!

        qtWidget = self._experiment.questionController.currentQuestion.qtWidget
        qtWidget.setMinimumWidth(self._maximumWidgetWidth)
        qtWidget.setMaximumWidth(self._maximumWidgetWidth)
        
        
        
        minimum_container_height = self._minimum_height-183
        
        if self._experiment.questionController.currentTitle:
            minimum_container_height = minimum_container_height-(self._title.height()+5)
            
        if self._experiment.questionController.currentSubtitle:
            minimum_container_height = minimum_container_height-(self._subTitle.height()+5)
            
        if self._experiment.questionController.currentStatustext:
            minimum_container_height = minimum_container_height-(self._status.height()+5)
            
        if not self._forwardButton.isVisible() and not self._backwardButton.isVisible() and not self._jumpBox.isVisible():
            minimum_container_height = minimum_container_height + 30
            
        qtWidget.setMinimumHeight(minimum_container_height)
        
        qtWidget.setParent(self._contentFrame)
        self._containerLayout.addWidget(qtWidget)
        self._contentFrame.show()
        qtWidget.show()
        
        # setzte oldQuestion
        self._oldQuestion = self._experiment.questionController.currentQuestion


    '''Abschnitt für selbstdefinierte Slots'''

    @Slot()
    def forwardClick(self):
        self._uiController.moveForward()

    @Slot()
    def backwardClick(self):
        self._uiController.moveBackward()
    
    @Slot()
    def jumpActivated(self, index):
        
        posList = self._jumpList[index][0]
        
        if posList[0] == -1:
            pass
        else: 
            self._uiController.moveToPosition(posList)

    @property
    def layoutWidget(self):
        return self._qtBaseWidget

    @property
    def maximumWidgetWidth(self):
        return self._maximumWidgetWidth
    
    def deactivate(self):
        
        super(BaseQtLayout, self).deactivate()
        
        
    '''
    init - super und dann anschließend layout (äußerer container) aus datei laden und slots (slots hier rufen funktionen im uiController auf) und signals managen
    render - update ui (mit altem inneren Container + Buttons können sich ändern und alle Texte, d.h. alle Texte im Layout und Buttons etc. werden aktualisiert - siehe WebLayout.render
    ACHTUNG: jumpList ist eine Liste von Tupeln mit Integers vorne und Text hinten - Funktionalität in altem Framework abschreiben. Wenn Item ausgewählt muss der entsprechende eintrag als PosList an UiController.moveToPosition übergeben werden!
    activate und deactivate müssen implementiert werden. Erst super aufrufen. Bei deactivate wird das aktuelle Widget erst freigegeben, bei activate muss einfach neu gerendert werden (evtl. mal testen ob überhaupt nötig)
    '''


class GoeWebLayout(Layout):
    def __init__(self):
        super(GoeWebLayout, self).__init__()
        self._style_urls = []
        self._js_urls = []
        self._template = jinja_env.get_template('goe_layout.html')

    def activate(self, experiment, uiController):
        super(GoeWebLayout, self).activate(experiment, uiController)
        # add css files
        self._style_urls.append((99,self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/goe_web_layout.css'), content_type="text/css")))
        self._style_urls.append((1,self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/bootstrap.min.css'), content_type="text/css")))
        self._style_urls.append((2,self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/jquery-ui.css'), content_type="text/css")))
        #self._style_urls.append(self._uiController.addStaticFile(os.path.join(package_path(), 'static/css/app.css'), content_type="text/css"))

        # add js files
        self._js_urls.append((01,
            self._uiController.addStaticFile(
                os.path.join(package_path(), 'static/js/jquery-1.8.3.min.js'),
                content_type="text/javascript")
            ))
        self._js_urls.append((02,self._uiController.addStaticFile(os.path.join(package_path(), 'static/js/bootstrap.min.js'), content_type="text/javascript")))
        self._js_urls.append((03,self._uiController.addStaticFile(os.path.join(package_path(), 'static/js/jquery-ui.js'), content_type="text/javascript")))

        self._js_urls.append((10,
            self._uiController.addStaticFile(
                os.path.join(package_path(), 'static/js/baseweblayout.js'),
                content_type="text/javascript")
            ))

        self._logo_url = self._uiController.addStaticFile(os.path.join(package_path(), 'static/img/uni_goe_logo.png'), content_type="image/png")

    @property
    def cssCode(self):
        return []

    @property
    def cssURLs(self):
        return self._style_urls

    @property
    def javascriptCode(self):
        return []

    @property
    def javascriptURLs(self):
        return self._js_urls

    def render(self):

        d = {}
        d['logo_url'] = self._logo_url
        d['widget'] = self._experiment.questionController.currentQuestion.webWidget

        if self._experiment.questionController.currentTitle:
            d['title'] = self._experiment.questionController.currentTitle

        if self._experiment.questionController.currentSubtitle:
            d['subtitle'] = self._experiment.questionController.currentSubtitle

        if self._experiment.questionController.currentStatustext:
            d['statustext'] = self._experiment.questionController.currentStatustext

        if not self._experiment.questionController.currentQuestion.canDisplayCorrectiveHintsInline \
                and self._experiment.questionController.currentQuestion.correctiveHints:
            d['corrective_hints'] = self._experiment.questionController.currentQuestion.correctiveHints

        if self.backwardEnabled and self._experiment.questionController.canMoveBackward:
            d['backward_text'] = self.backwardText

        if self.forwardEnabled:
            if self._experiment.questionController.canMoveForward:
                d['forward_text'] = self.forwardText
            else:
                if not self._finishedDisabled:
                    d['finish_text'] = self.finishText

        if self.jumpListEnabled and self._experiment.questionController.jumplist:
            jmplist = self._experiment.questionController.jumplist
            for i in range(len(jmplist)):
                jmplist[i] = list(jmplist[i])
                jmplist[i][0] = '.'.join(map(str, jmplist[i][0]))
            d['jumpList'] = jmplist

        messages = self._experiment.messageManager.getMessages()
        if messages:
            for message in messages:
                message.level = '' if message.level == 'warning' else 'alert-' + message.level # level to bootstrap
            d['messages'] = messages


        return self._template.render(d)


    @property
    def backwardLink(self):
        return self._backwardLink
    @backwardLink.setter
    def backwardLink(self, link):
        self._backwardLink = link

    @property
    def forwardLink(self):
        return self._forwardLink
    @forwardLink.setter
    def forwardLink(self, link):
        self._forwardLink = link
