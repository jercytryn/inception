from PySide import QtCore, QtGui
from .base import AbstractSelectionTool

class SelectionTool(AbstractSelectionTool):
    name = "selection"
    
    enableCopyCuts = QtCore.Signal(bool)
    enableSelectionTool = QtCore.Signal(bool)
    
    def __init__(self, *args, **kwargs):
        super(SelectionTool, self).__init__(*args, **kwargs)
        
        self._selectedImage = None
        self._pasteImage = None
        self.options = {}
    
    def copyImage(self, imageWidget):
        if self._hasSelection:
            imageWidget.setImage(self._imageCopy)
            clipboard = QtGui.QApplication.clipboard()
            copyImage = None
            if self._imageSelected:
                copyImage = self._selectedImage
            else:
                copyImage = imageWidget.getImage().copy(self._topLeftPoint.x(), self._topLeftPoint.y(),
                                                        self._width, self._height)
            
            clipboard.setImage(copyImage, QtGui.QClipboard.Clipboard)
    
    def cutImage(self, imageWidget):
        if self._hasSelection:
            self.copyImage(imageWidget)
            imageWidget.setImage(self._imageCopy)
            self.paint(imageWidget)
        
        if self._imageSelected:
            imageWidget.setImage(self._imageCopy)
        else:
            self.clearSelectionBackground(imageWidget)
        self._topLeftPoint = QtCore.QPoint(0,0)
        self._bottomRightPoint = QtCore.QPoint(0,0)
        self._imageCopy = imageWidget.getImage()    
        imageWidget.update()
        imageWidget.restoreCursor()
        self._hasSelection = False
        self.enableCopyCuts.emit(False)
    
    def pasteImage(self, imageWidget):
        clipboard = QtGui.QApplication.clipboard()
        if (self._hasSelection):
            imageWidget.setImage(self._imageCopy)
            self.paint(imageWidget)
            self._imageCopy = imageWidget.getImage()
        self._pasteImage = clipboard.image()
        if not self._pasteImage.isNull():
            self._selectedImage = self._pasteImage
            self._imageCopy = imageWidget.getImage()
            self._topLeftPoint = QtCore.QPoint(0,0)
            self._bottomRightPoint = QtCore.QPoint(self._pasteImage.width(), self._pasteImage.height() - QtCore.QPoint(1,1))
            self._height = self._pasteImage.height()
            self._width = self._pasteImage.width()
            self._imageSelected = True
            self._hasSelection = True
            self.paint(imageWidget)
            self.drawBorder(imageWidget)
            imageWidget.restoreCursor()
            self.enableCopyCuts.emit(True)
    
    def beginAdjustment(self, widget):
        self._imageCopy = widget.getImage()
        self._imageSelected = False
        
    def beginResize(self, widget):
        if not self._imageSelected:
            self.clearSelectionBackground(widget)
        if self._selectionAdjusting:
            self._imageSelected = False
    
    def beginMoving(self, widget):
        self.clearSelectionBackground(widget)
        if self._selectionAdjusting:
            self._imageSelected = False
    
    def endSelection(self, widget):
        self._cacheSelectedImage(widget)
        self.enableCopyCuts.emit(True)
    
    def endResize(self, widget):
        self._cacheSelectedImage(widget)
    
    def endMoving(self, widget):
        if self._selectionAdjusting:
            self._cacheSelectedImage(widget)
    
    def clearSelectionBackground(self, imageWidget):
        if self._selectionAdjusting:
            painter = QtGui.QPainter(imageWidget.getImage())
            painter.setPen(QtCore.Qt.white)
            painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
            painter.setBackgroundMode(QtCore.Qt.OpaqueMode)
            painter.drawRect(QtCore.QRect(self._topLeftPoint, self._bottomRightPoint - QtCore.QPoint(1,1)))
            painter.end()
            self._imageCopy = imageWidget.getImage()
    
    def clear(self):
        self._selectedImage = QtGui.QImage()
        self.enableCopyCuts.emit(False)
        
    def paint(self, widget, *args, **kwargs):
        if (self._hasSelection and not self._selectionAdjusting):
            if self._topLeftPoint != self._bottomRightPoint:
                painter = QtGui.QPainter(widget.getImage())
                source = QtCore.QRect(0,0,self._selectedImage.width(),self._selectedImage.height())
                target = QtCore.QRect(self._topLeftPoint, self._bottomRightPoint)
                painter.drawImage(target, self._selectedImage, source)
                painter.end()
            widget.setEdited(True)
            widget.update()
    
    def _cacheSelectedImage(self, widget):
        self._selectedImage = widget.getImage().copy(self._topLeftPoint.x(),
                                                     self._topLeftPoint.y(),
                                                     self._width, self._height)
                