# -*- coding: utf-8 -*-
'''
Created on 08.07.2012

@author: ChristianT
'''

from threading import Thread, currentThread, Event
from PySide.QtCore import QObject, Signal
from PySide import QtCore

import alfred.settings

if alfred.settings.experiment.type == 'web':
    class AsyncTask(object):
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Do not use this class in Webexperiments.")
            
elif alfred.settings.experiment.type != 'web':


    class AsyncTask(QObject):
        '''
        Implementiert werden nur die On... Funktionen (optional)
        und doInBackground (zwingend)
        
        AsynTasks müssen als Membervariablen von Klasse (self.) 
        oder als globale Variablen deklariert werden!
        
        '''

        # Definieren der relevanten Signale für Qt
        
        onPreExecuteSignal = Signal()
        onProgressUpdateSignal = Signal(object)
        onPostExecuteSignal = Signal(object)
        onCancelledSignal = Signal(object)
        
        
        def __init__(self, slot = None, references = None):
            super(AsyncTask, self).__init__()
            self._thread = None
            self._validateNotSelfThread()
            self._isCancelled = Event()
            self._result = None
            self._references = references
            self.onPreExecuteSignal.connect(self._onPreExecute)
            self.onProgressUpdateSignal.connect(self._onProgressUpdate) 
            self.onPostExecuteSignal.connect(self._onPostExecute) 
            self.onCancelledSignal.connect(self._onCancelled)  
        
        def cancel(self, interruptRunning=False):
            self._validateNotSelfThread()
            self._isCancelled.set()
        
        def execute(self, params = None):
            self._validateNotSelfThread()
            self._thread = Thread(target = self._doInBackground, args=[params], kwargs=None)
            self.onPreExecuteSignal.emit()
            self._thread.start()
        
        def get(self, timeout = None):
            self._validateNotSelfThread()
            self._thread.join(timeout)
            
            if self._isCancelled.isSet():
                raise 'Cancellation Exception'
            
            if self.getStatus():
                raise 'Timeout Exception'
            
            return self._result
        
        def getStatus(self):
            self._validateNotSelfThread()
            return self._thread.isAlive()
        
        def isCancelled(self):
            return self._isCancelled.isSet()
        
        def doInBackground(self,params):
            raise 'Abstract Method'
            
        def _validateNotSelfThread(self):
            assert currentThread().getName() != self._thread.getName() if self._thread is not None else True
        
        def _doInBackground(self,params):
            result = self.doInBackground(params)
            self._result = result
            
            if result is None:
                result = 'None'
            
            if not self._isCancelled.isSet():
                self.onPostExecuteSignal.emit(result)  
            
            elif self._isCancelled.isSet():
                self.onCancelledSignal.emit(result)
                
        def publishProgress(self, values):
            if values is None:
                values = 'None'
            self.onProgressUpdateSignal.emit(values)
         
        #Definition der verbundenen QtCore Slots
        
        @QtCore.Slot()    
        def _onPreExecute(self):
            self.onPreExecute()
        
        @QtCore.Slot(object)
        def _onProgressUpdate(self,values):
            self.onProgressUpdate(values)
        
        @QtCore.Slot(object)
        def _onPostExecute(self,result):
            self.onPostExecute(result)
        
        @QtCore.Slot(object)
        def _onCancelled(self,result):
            self.onCancelled(result)
        
        
        #Definition der abstrakten Methoden zur späteren Implementierung
        
        def onPreExecute(self):
            pass
        
        def onProgressUpdate(self, values):
            pass
        
        def onPostExecute(self, result):
            pass
        
        def onCancelled(self, result):
            pass
        
