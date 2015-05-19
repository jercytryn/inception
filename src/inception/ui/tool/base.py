
from PySide import QtGui, QtCore

_padding = 6

class AbstractTool(QtCore.QObject):
    name = None
    
    def __init__(self, *args, **kwargs):
        super(AbstractTool, self).__init__(*args, **kwargs)
        
        self._startDrawPoint, self._endDrawPoint = None, None
        self._imageCopy = None
        self._width = self._height = 0, 0
        
    def reset(self):
        self._startDrawPoint, self._endDrawPoint = None, None
        self._imageCopy = None
        self._width = self._height = 0, 0
        
    def update(self, *args, **kwargs):
        pass

class AbstractSelectionTool(AbstractTool):
    name = None
    
    def __init__(self, *args, **kwargs):
        super(AbstractSelectionTool, self).__init__(*args, **kwargs)
        
        self._hasSelection = False
        self._selectionMoving = False
        self._selectionResizing = False
        self._selectionAdjusting = False
        self._mouseMoving = False
        self._imageSelected = False
        self._painting = False
        self._button = None
        self.source = None
        
        self._bottomRightPoint = self._topLeftPoint = None
        self._diffPoint = None
        
    def mousePressEvent(self, mouseEvent, imageWidget):
        self._button = mouseEvent.button()
        self._mouseMoving = False
        if self._hasSelection:
            imageWidget.setImage(self._imageCopy)
            self.paint(imageWidget)
            if self._button == QtCore.Qt.RightButton:
                self._selectionAdjusting = True
                self.beginAdjustment(imageWidget)
            
            if mouseEvent.pos().x() > self._topLeftPoint.x() and \
                    mouseEvent.pos().x() < self._bottomRightPoint.x() and \
                    mouseEvent.pos().y() > self._topLeftPoint.y() and \
                    mouseEvent.pos().y() < self._bottomRightPoint.y():
                if not self._imageSelected:
                    self.beginMoving(imageWidget)
                    if self._selectionAdjusting:
                        self._imageSelected = True
                else:
                    self.drawBorder(imageWidget)
                self._selectionMoving = True
                self._diffPoint = self._bottomRightPoint - mouseEvent.pos()
                return
            elif mouseEvent.pos().x() >= self._bottomRightPoint.x() and \
                    mouseEvent.pos().x() <= self._bottomRightPoint.x() + _padding and \
                    mouseEvent.pos().y() >= self._bottomRightPoint.y() and \
                    mouseEvent.pos().y() <= self._bottomRightPoint.y() + _padding:
                self.beginResize(imageWidget)
                self._selectionResizing = True
                return
            else:
                self.clearSelection(imageWidget)
                
        if self._button == QtCore.Qt.LeftButton:
            self._bottomRightPoint = mouseEvent.pos()
            self._topLeftPoint = mouseEvent.pos()
            self._width = 0
            self._height = 0 
            self._imageCopy = imageWidget.getImage()
            
            self.beginSelection(imageWidget)
            self._painting = True
            
    def mouseMoveEvent(self, mouseEvent, imageWidget):
        modifiers = QtGui.QApplication.keyboardModifiers()
        
        self._mouseMoving = True
        if self._hasSelection:
            if self._selectionMoving:
                self._bottomRightPoint = mouseEvent.pos() + self._diffPoint
                self._topLeftPoint = mouseEvent.pos() + self._diffPoint - QtCore.QPoint(self._width - 1, self._height - 1)

                imageWidget.setImage(self._imageCopy)
                self.move(imageWidget)
            
                self.drawBorder(imageWidget)
                self._painting = False
            elif self._selectionResizing:
                self._bottomRightPoint = mouseEvent.pos()
                self._height = abs(self._bottomRightPoint.y() - self._topLeftPoint.y()) + 1
                self._width = abs(self._bottomRightPoint.x() - self._topLeftPoint.x()) + 1
                                
                imageWidget.setImage(self._imageCopy)
                self.resize(imageWidget)
                self.drawBorder(imageWidget)
                self._painting = False
                
        if self._painting:
            self._bottomRightPoint = mouseEvent.pos()
            self._height = abs(self._bottomRightPoint.y() - self._topLeftPoint.y()) + 1
            self._width = abs(self._bottomRightPoint.x() - self._topLeftPoint.x()) + 1     
            
            if modifiers == QtCore.Qt.ControlModifier and self.source:
                self._width = 1 + self._height * (self.source.width / float(self.source.height))
                self._bottomRightPoint.setX(self._topLeftPoint.x() + self._width)
                  
            imageWidget.setImage(self._imageCopy)
            self.drawBorder(imageWidget)
            self.select(imageWidget)
        
        self.updateCursor(mouseEvent, imageWidget)
        
    def mouseReleaseEvent(self, mouseEvent, imageWidget):
        if self._topLeftPoint and self._bottomRightPoint:
            right = self._topLeftPoint.x() if self._topLeftPoint.x() > self._bottomRightPoint.x() else self._bottomRightPoint.x()
            bottom = self._topLeftPoint.y() if self._topLeftPoint.y() > self._bottomRightPoint.y() else self._bottomRightPoint.y()
            left = self._topLeftPoint.x() if self._topLeftPoint.x() < self._bottomRightPoint.x() else self._bottomRightPoint.x()
            top = self._topLeftPoint.y() if self._topLeftPoint.y() < self._bottomRightPoint.y() else self._bottomRightPoint.y()
        self._bottomRightPoint = QtCore.QPoint(right, bottom)
        self._topLeftPoint = QtCore.QPoint(left, top)
        if self._hasSelection:
            self.updateCursor(mouseEvent, imageWidget)
    
            if self._button == QtCore.Qt.RightButton and not self._mouseMoving:
                self.showMenu(imageWidget)
                self.paint(imageWidget)
                self.drawBorder(imageWidget)
                self._painting = False
                self._selectionMoving = False
                self._hasSelection = False
            elif self._selectionMoving:
                imageWidget.setImage(self._imageCopy)
                self.endMoving(imageWidget)
                self.paint(imageWidget)
                self.drawBorder(imageWidget)
                self._painting = False
                self._selectionMoving = False
            elif self._selectionResizing:
                imageWidget.setImage(self._imageCopy)
                self.paint(imageWidget)
                self.endResize(imageWidget)
                self.paint(imageWidget)
                self.drawBorder(imageWidget)
                self._painting = False
                self._selectionResizing = False
        
        if (self._painting):
            if mouseEvent.button() == QtCore.Qt.LeftButton:
                imageWidget.setImage(self._imageCopy)
                if (self._topLeftPoint != self._bottomRightPoint):
                    imageWidget.setImage(self._imageCopy)
                    self.paint(imageWidget)
                    self.endSelection(imageWidget)
                    self.paint(imageWidget)
                    self._hasSelection = True
                self.drawBorder(imageWidget)
                self._painting = False
                
        self._selectionAdjusting = False
    
    def drawBorder(self, widget):
        if self._width > 1 and self._height > 1:
            painter = QtGui.QPainter(widget.getImage())
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DashLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
            painter.setBackgroundMode(QtCore.Qt.OpaqueMode)
            if self._topLeftPoint != self._bottomRightPoint:
                painter.drawRect(QtCore.QRect(self._topLeftPoint, self._bottomRightPoint - QtCore.QPoint(1,1)))
            widget.setEdited(True)
            painter.end()
            widget.update()
    
    def clearSelection(self, widget):
        if self._hasSelection:
            widget.setImage(self._imageCopy)
            self.paint(widget)
            self._selectionMoving = False
            self._selectionResizing = False
            self._painting = False
            self._imageSelected = False
            self._imageCopy = None
            widget.update()
            widget.restoreCursor()
            self.clear()
        
    def updateCursor(self, event, imageWidget):
        if self._hasSelection:
            if event.pos().x() > self._topLeftPoint.x() and \
                    event.pos().x() < self._bottomRightPoint.x() and \
                    event.pos().y() > self._topLeftPoint.y() and \
                    event.pos().y() < self._bottomRightPoint.y():
                imageWidget.setCursor(QtCore.Qt.SizeAllCursor)
            elif event.pos().x() >= self._bottomRightPoint.x() and \
                    event.pos().x() <= self._bottomRightPoint.x() + _padding and \
                    event.pos().y() >= self._bottomRightPoint.y() and \
                    event.pos().y() <= self._bottomRightPoint.y() + _padding:
                imageWidget.setCursor(QtCore.Qt.SizeFDiagCursor)
            else:
                imageWidget.restoreCursor()
        else:
            imageWidget.restoreCursor()
        
    def beginResize(self, widget):
        pass
    
    def endResize(self, widget):
        pass
    
    def beginMoving(self, widget):
        pass
    
    def endMoving(self, widget):
        pass
    
    def beginAdjustment(self, widget):
        pass
    
    def beginSelection(self, widget):
        pass
    
    def endSelection(self, widget):
        pass
    
    def move(self, widget):
        pass
    
    def resize(self, widget):
        pass
            
    def select(self, widget):
        pass
    
    def clear(self):
        pass
    
    def showMenu(self, widget):
        pass
    
    def paint(self, *args, **kwargs):
        raise NotImplementedError()