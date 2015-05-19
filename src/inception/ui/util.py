import os
import sys

__all__ = ['loadUi']

from PySide import QtCore, QtGui, QtUiTools

class AutoUiLoader(QtUiTools.QUiLoader):
    """
    A class for dynamically loading a ui file at runtime
    """

    def __init__(self, base):
        super(AutoUiLoader, self).__init__(base)
        self.base = base

    def createWidget(self, cls, parent=None, name=''):
        if parent is None:
            return self.base
        
        widget = super(AutoUiLoader, self).createWidget(cls, parent, name)
        setattr(self.base, name, widget)
        return widget

def loadUi(uifile, baseinstance=None):
    """
    Loads the given ui filepath into the given instance
    E.g. from within a subclass of QWidget:
    
    >>> loadUi(os.path.join(_scriptDir, 'mywidget.ui'), self)
    
    The instance will then have access to all child widgets in the ui file
    Slots are automatically connected based on the name of objects/signals
    in the ui files. E.g. on_actionOpen_triggered
    """
    loader = AutoUiLoader(baseinstance)
    widget = loader.load(uifile)
    QtCore.QMetaObject.connectSlotsByName(widget)
    return widget

