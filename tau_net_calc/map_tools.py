
from qgis.gui import QgsMapTool
from qgis.utils import iface
from qgis.PyQt import QtCore


class SendPointToolCoordinates(QgsMapTool):
    """ Enable to return coordinates from clic in a layer.
    """
    def __init__(self, canvas, layer,callBack):
        """ Constructor.
        """
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer
        self.setCursor(QtCore.Qt.CrossCursor)
        self.callBack=callBack
    
    def canvasReleaseEvent(self, event):
        point = self.toLayerCoordinates(self.layer, event.pos())
        self.clicked_point = point 
        #print(point.x(), point.y())
        # self.dlg.lineEdit.setText(str(point.x()))
        self.callBack(point.x(),point.y())

#layer, canvas = iface.activeLayer(), iface.mapCanvas()

#send_point_tool_coordinates = SendPointToolCoordinates(
 #   canvas,
  #  layer
#)
#canvas.setMapTool(send_point_tool_coordinates)