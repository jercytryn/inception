from PySide import QtCore, QtGui
from .base import AbstractSelectionTool
from inception.image import Image
from inception.image.operation import floodfill, scale, poisson, merge, statadjust, shadow
from inception.image.analyze import estimate_scene_description

class InsertionTool(AbstractSelectionTool):
    name = "insertion"
    
    def __init__(self, *args, **kwargs):
        super(InsertionTool, self).__init__(*args, **kwargs)   
        self.insertionThread = InsertionThread(parent=self)
        self.insertionThread.finished.connect(self.insertionDone)
        
        self._scene_description = None
        self.source = None
    
    def reset(self):
        super(InsertionTool, self).reset()
        self._scene_description = None
    
    def endSelection(self, widget):
        if not self.insertionThread.isRunning():
            self.insertionThread.srcImage = self.source
            self.insertionThread.options = self.options
            self.insertionThread.destImage = Image.from_qimage(self._imageCopy)
            self.insertionThread.destImage.scene_description = self._scene_description
            self.insertionThread.bbox = (self._topLeftPoint.x(), self._topLeftPoint.y(), self._bottomRightPoint.x(), self._bottomRightPoint.y())
            self.insertionThread.widget = widget
            self.insertionThread.start()
        
    def insertionDone(self):
        finalImage = self.insertionThread.compImage
        self._imageCopy = finalImage.qimage
        self._scene_description = finalImage.scene_description
        self.insertionThread.widget.setImage(self._imageCopy)
        self._scene_description = self.insertionThread.destImage.scene_description

        self.insertionThread.widget.update()
        
    def endResize(self, widget):
        pass
    
    def endMoving(self, widget):
        pass
    
    def clearSelectionBackground(self, imageWidget):
        pass

    def paint(self, widget, *args, **kwargs):
        pass
    
    def setSourceImage(self, source):
        self.source = source
    
    def setOptions(self, **kwargs):
        self.options = kwargs
    
    def update(self, filepath):
        self.setSourceImage(Image.from_filepath(filepath))

class InsertionThread(QtCore.QThread):
    def __init__(self, parent=None):
        super(InsertionThread, self).__init__(parent=parent)
        
        self.options = None
        self.srcImage = None
        self.bbox = None
        self.destImage = None
        self.compImage = None
        self.widget = None
        
    def run(self):
        # step 1: floodfill the source image
        print("Matting: %s" % self.options['matteOp'])
        mattingOps = self.options['matteOp']
        image = self.srcImage
        for opCls in mattingOps:        
            op = opCls(self.srcImage)
            image = op.run()
        
        # step 2: scale the source image
        width = self.bbox[2] - self.bbox[0] + 1
        height = self.bbox[3] - self.bbox[1] + 1
        scaleOp = scale.ScaleOperation(image, width, height)
        result = scaleOp.run()
        
        # generate shadow
        genshadow = None
        if self.options['shadows']:
            print("Generating shadow...")
            # cache scene description
            if self.destImage.scene_description is None:
                print("Caching scene description...")
                self.destImage.scene_description = estimate_scene_description(self.destImage)
            genshadow = shadow.GenerateShadowOperation(result, self.destImage, offset=(self.bbox[1], self.bbox[0])).run()    
            print("Generated shadow %s" % genshadow)    
        
        if self.options['statAdjust']:
            result = statadjust.StatAdjustOperation(result, self.destImage, offset=(self.bbox[1], self.bbox[0])).run()
        
        # step 3: poisson blend/merge with the dest image
        print("Merge: %s" % self.options['mergeOp'])
        if issubclass(self.options['mergeOp'], merge.MergeOperation):
            args = [[self.destImage, result]]
            offsets=[(0,0),(self.bbox[1], self.bbox[0])]
            if self.options['shadows']:
                args[0].insert(1, genshadow)
                offsets.insert(1, (0,0))
            kwargs = dict(offsets=offsets)
        else:
            # TODO: support shadows (will require poisson not to merge itself or similar)
            args = [result, self.destImage]
            kwargs = dict(offset=(self.bbox[1], self.bbox[0]))
        
        op = self.options['mergeOp'](*args, **kwargs)
        op.run()
        
        self.compImage = op.opimage
        
        