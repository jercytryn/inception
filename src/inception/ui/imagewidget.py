import os
import inception.ui.resources
from PySide import QtGui, QtCore
from .tool.selection import SelectionTool
from inception.ui.tool.insert import InsertionTool
from inception.image import Image

_padding = 5

# much of the gui framework infrastructure was adapted from or inspired by 
# https://github.com/Gr1N/EasyPaint, a qt-based paint system

class ImageWidget(QtGui.QWidget):
    """
    The widget within the main GUI that contains the rendered image
    """
    
    enableCopyCuts = QtCore.Signal(bool)
    enableSelectionTool = QtCore.Signal(bool)
    toolSet = QtCore.Signal(str)
    cursorPositionSent = QtCore.Signal(QtCore.QPoint)
    
    def __init__(self, open=None, parent=None):
        super(ImageWidget, self).__init__(parent=parent)
        
        self.setMouseTracking(True)
        self._rightButtonPressed = False
        self._filepath = None
        self._image = None
        self._clipboardImage = None
        self._zoomFactor = 1
        self._dirty = False
        self._resize = False
        
        self.par = parent
        
        self.initImage()
        
        if open:
            self.open(open)
        else:
            width, height = self.getDefaultImageSize()
            clipboard = QtGui.QApplication.clipboard()
            self._clipboardImage = clipboard.image()
            if not self._clipboardImage.isNull():
                width, height = self._clipboardImage.width(), self._clipboardImage.height()
            
            painter = QtGui.QPainter(self._image)
            painter.fillRect(0, 0, width, height, QtCore.Qt.white)
            painter.end()
            
            self.resize(self._image.rect().right() + _padding,
                        self._image.rect().bottom() + _padding)
            
        self._selectionTool = SelectionTool(self)
        self._selectionTool.enableCopyCuts.connect(self.enableCopyCuts)
        self._selectionTool.enableSelectionTool.connect(self.enableSelectionTool)
        
        self.tools = {'cursor':self._selectionTool, 'selection':self._selectionTool,
                      'insertion':InsertionTool(self)}
        self.currentTool = None
        self.currentToolName = None
    
    def initImage(self):
        width, height = self.getDefaultImageSize()
        self._image = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32_Premultiplied)
        
    def getDefaultImageSize(self):
        return (300, 300)
    
    def setCurrentTool(self, name, *args, **kwargs):
        if name in self.tools:  
            self.currentTool = self.tools[name]
            self.currentToolName = name
            self.currentTool.update(*args, **kwargs)
        else:
            self.currentTool = None
            self.currentToolName = None
    
    def open(self, filepath):
        success = True
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            if self._image.load(filepath):
                self._image = self._image.convertToFormat(QtGui.QImage.Format_ARGB32_Premultiplied)
                self._filepath = filepath
                self.resize(self._image.rect().right() + _padding,
                            self._image.rect().bottom() + _padding)
                
                if hasattr(self, 'tools'):
                    for tool in self.tools.values():
                        tool.reset()
                
            else:
                print("Could not open file '%s'" % filepath)
                success = False
        finally:
            QtGui.QApplication.restoreOverrideCursor()
        
        if not success:
            QtGui.QMessageBox.warning(self, "File open error", "Could not open file '%s'" % filepath)
    
    def save(self, path):
        path = os.path.abspath(path)
        parent = os.path.dirname(path)
        if not os.path.exists(parent):
            os.makedirs(parent)
        Image.from_qimage(self._image).save(path)
    
    def copyImage(self):
        self.tools['cursor'].copyImage()
        
    def pasteImage(self):
        if self.currentTool != self.tools['cursor']:
            self.toolSet.emit('cursor')
        self.tools['cursor'].pasteImage()
        
    def cutImage(self):
        self.tools['cursor'].cutImage()
        
    def mousePressEvent(self, mouseEvent):
        if mouseEvent.button == QtCore.Qt.LeftButton and \
                mouseEvent.pos().x() < self._image.rect().right() + _padding and \
                mouseEvent.pos().x() > self._image.rect().right() and \
                mouseEvent.pos().y() > self._image.rect().bottom() and \
                mouseEvent.pos().y() < self._image.rect().bottom() + _padding:
            self._resize = True
            self.setCursor(QtCore.Qt.SizeFDiagCursor)
        elif self.currentTool:
            self.currentTool.mousePressEvent(mouseEvent, self)
    
    def mouseMoveEvent(self, mouseEvent):
        if self._resize:
            print("Resizing not implemented")
        elif mouseEvent.pos().x() < self._image.rect().right() + _padding and \
                mouseEvent.pos().x() > self._image.rect().right() and \
                mouseEvent.pos().y() > self._image.rect().bottom() and \
                mouseEvent.pos().y() < self._image.rect().bottom() + _padding:
            self.setCursor(QtCore.Qt.SizeFDiagCursor)
            return
        elif not self.currentTool:
            self.restoreCursor()
        if mouseEvent.pos().x() < self._image.width() and mouseEvent.pos().y() < self._image.height():
            self.cursorPositionSent.emit(mouseEvent.pos())
        
        if self.currentTool:
            self.currentTool.mouseMoveEvent(mouseEvent, self)
            pass
    
    def mouseReleaseEvent(self, mouseEvent):
        if self._resize:
            self._resize = False
            self.restoreCursor()
        elif self.currentTool:
            if self.currentToolName == 'insertion':
                self.currentTool.setOptions(**self.getParentOptions(self.currentToolName))
            self.currentTool.mouseReleaseEvent(mouseEvent, self)

    def getParentOptions(self, toolname):
        return self.par.getOptions(toolname)
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        painter.drawRect(0,0, self._image.rect().right() - 1, self._image.rect().bottom() - 1)
        painter.drawImage(event.rect(), self._image, event.rect())
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.black))
        painter.drawRect(QtCore.QRect(self._image.rect().right(), self._image.rect().bottom(), _padding, _padding))
        painter.end()
    
    def restoreCursor(self):
        if not self.currentTool:
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        elif self.currentTool.name == 'selection':
            self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        elif self.currentTool.name == 'insertion':
            self.setCursor(QtGui.QPixmap(':icons/icons/light105.png'))
        else:
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
    
    def drawCursor(self):
        pass
    
    def clearSelection(self):
        if self.currentTool:
            self.currentTool.clearSelection(self)

    def getImage(self):
        return self._image
    
    def setImage(self, image):
        if image is not None:
            self._image = image.copy()
    
    def setEdited(self, edited=True):
        pass
    
    def zoomIn(self, factor=1.5):
        self.zoom(factor)
    
    def zoomOut(self, factor=1.5):
        self.zoom(1.0/factor)
    
    def zoom(self, factor):
        self.setImage(self.getImage().transformed(QtGui.QTransform.fromScale(factor, factor)))
        self.resize(self._image.rect().right() + _padding,
                            self._image.rect().bottom() + _padding)
        self.setEdited(True)
        self.clearSelection()
        self.update()
        
        