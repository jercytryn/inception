import sys, os, logging
import inception.ui.resources

from PySide import QtCore, QtGui
from inception.ui.util import loadUi
from .imagewidget import ImageWidget
from ..image.operation import merge, matte, floodfill, poisson, grabcut

_scriptDir = os.path.dirname(os.path.abspath(__file__))

# much of the gui framework infrastructure was ported from or inspired by 
# https://github.com/Gr1N/EasyPaint, a qt-based paint system

class InceptionMainWindow(QtGui.QMainWindow):
    """
    The main inception ui
    """
    def __init__(self, defaultFilepath=None, parent=None):
        super(InceptionMainWindow, self).__init__(parent=parent)
        loadUi(os.path.join(_scriptDir, 'mainwidget.ui'), self)
        
        self.imageWidget = ImageWidget(open=defaultFilepath, parent=self)
        self.scrollArea.setWidget(self.imageWidget)
        
        self.connectSignals()
        
    def connectSignals(self):
        self.zoomInShortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+="), self)
        self.zoomInShortcut.activated.connect(self.zoomIn)
        self.zoomOutShortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self)
        self.zoomOutShortcut.activated.connect(self.zoomOut)
        self.fileBrowseButton.clicked.connect(self.filebrowseButton_triggered)
    
    @QtCore.Slot()
    def zoomIn(self):
        self.imageWidget.zoomIn()
        
    @QtCore.Slot()
    def zoomOut(self):
        self.imageWidget.zoomOut()
    
    @QtCore.Slot()
    def on_actionOpen_triggered(self):
        dirpath = os.path.join(os.path.dirname(__file__),"../../../bg")
        if not os.path.exists(dirpath):
            try:
                os.makedirs(dirpath)
            except OSError:
                logging.warn("Could not make directory %s" % os.path.abspath(dirpath))
        
        result = QtGui.QFileDialog.getOpenFileName(self, "Open background image",
                                                   filter="Image (*.png *.jpg *.jpeg);; PNG (*.png);; JPEG (*.jpg *.jpeg)",
                                                   dir=dirpath)
        if result[0]:
            self.imageWidget.open(result[0])
    
    @QtCore.Slot()
    def on_actionExport_As_triggered(self):
        dirpath = os.path.join(os.path.dirname(__file__),"../../../output")
        if not os.path.exists(dirpath):
            try:
                os.makedirs(dirpath)
            except OSError:
                logging.warn("Could not make directory %s" % os.path.abspath(dirpath))
        
        result = QtGui.QFileDialog.getSaveFileName(self, "Save composite image",
                                                   filter="PNG (*.png);; JPEG (*.jpg *.jpeg);; Bitmap (*.bmp)",
                                                   dir=dirpath)
        if result[0]:
            self.imageWidget.save(result[0])
    
    @QtCore.Slot()
    def on_actionSelect_triggered(self):
        self.imageWidget.setCurrentTool('selection')
        self.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        
    @QtCore.Slot()
    def on_actionCursor_triggered(self):
        self.imageWidget.setCurrentTool(None)
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
    
    @QtCore.Slot()
    def on_actionInsert_triggered(self):
        self.setCursor(QtGui.QPixmap(':icons/icons/light105.png'))

        if self.insertImageLabel.text().strip() == 'Choose an image':
            # a default image to use for insertion
            filepath = os.path.join(os.path.dirname(__file__),"../../../test/images/traditional-buffets-and-sideboards.jpg")
            if os.path.exists(filepath):
                self.imageWidget.setCurrentTool('insertion', filepath)
                self.insertImageLabel.setText(filepath.split('/')[-1])
                
    @QtCore.Slot()
    def filebrowseButton_triggered(self):
        dirpath = os.path.join(os.path.dirname(__file__),"../../../fg")
        if not os.path.exists(dirpath):
            try:
                os.makedirs(dirpath)
            except OSError:
                logging.warn("Could not make directory %s" % os.path.abspath(dirpath))
        result = QtGui.QFileDialog.getOpenFileName(self, "Open background image",
                                                   filter="Image (*.png *.jpg *.jpeg);; PNG (*.png);; JPEG (*.jpg *.jpeg)",
                                                   dir=dirpath)
        if result[0]:
            self.imageWidget.setCurrentTool('insertion', result[0])
            self.insertImageLabel.setText(result[0].split('/')[-1])

    def getOptions(self, toolname):
        if toolname == 'insertion':
            return {'mergeOp':self.getMergeOpFromName(self.mergeComboBox.currentText()),
                    'matteOp':self.getMatteOpFromName(self.mattingComboBox.currentText()),
                    'statAdjust':self.colorAdjustCheckBox.isChecked(),
                    'shadows':self.shadowsCheckBox.isChecked()
                    }
        
        return {}
    
    def getMergeOpFromName(self, name):
        if name == 'merge':
            return merge.MergeOperation
        elif name == 'poisson':
            return poisson.PoissonOperation
    
    def getMatteOpFromName(self, name):
        if name == 'none':
            return []
        elif name == 'floodfill':
            return [floodfill.FloodfillOperation]
        elif name == 'simplematting':
            return [matte.SimpleMatteOperation]
        elif name == 'closedform':
            return [matte.ClosedFormMatteOperation]
        elif name == 'grabcut':
            return [grabcut.GrabcutMatteOperation]

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = InceptionMainWindow("../../../test/images/traditional-living-room.jpg")
    window.show()
    sys.exit(app.exec_())