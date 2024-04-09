
from qgis.core import   QgsPointXY, QgsGeometry,QgsFeatureRequest,QgsDistanceArea, QgsProject,QgsCoordinateTransform, QgsPointXY,QgsCoordinateReferenceSystem
import math 
#from geopy.distance import distance
from pyproj import Proj, transform

class SpatialQueries():
    
   def __init__(self, layer):
         self.layer = layer
         #self.callBack=callBack

   def selectFromLayerBycircle(self,xCenter,yCenter,radius):
     #areaOfInterest = QgsCircle(QgsPoint(xCenter, yCenter), radius)
     geometry = QgsGeometry.fromPointXY(QgsPointXY(xCenter,yCenter))
     request = QgsFeatureRequest().setDistanceWithin(geometry,radius)
     return self.layer.getFeatures(request)
    
    
  #  def meters_to_degrees(self,meters, point_layer):
  #   # Get the CRS of the point layer
  #   crs = point_layer.crs()

  #   # Create a coordinate transform from layer CRS to EPSG:4326 (WGS84)
  #   transform = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())

  #   # Get the center point of the layer's extent
  #   center_point = QgsPointXY(point_layer.extent().center())

  #   # Convert the center point to EPSG:4326
  #   center_point_4326 = transform.transform(center_point)

  #   # Get the latitude at the center point
  #   latitude = center_point_4326.y()

  #   # Calculate the conversion factor
  #   conversion_factor = meters / QgsDistanceArea.measureLine(latitude, 0, latitude, 1)

  #   # Convert the distance in meters to degrees
  #   degrees = meters / conversion_factor

  #   return degrees
   
   def metersToDecimalDegrees(self, meters, latitude):

    #return meters / (111.32 * 1000 * math.cos(latitude * (math.pi / 180)));
    return meters / (111.32 * 1000 )
   
   import math

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance (in kilometers) between two points
    on the Earth's surface specified by longitude and latitude (in degrees).
    """
    # Convert degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Radius of the Earth (mean value in kilometers)
    radius = 6371  # Earth's radius in kilometers

    # Calculate the distance
    distance = radius * c

    return distance

# # Example: Calculate the distance between two points
# lon1 = -73.9616  # Longitude of point 1
# lat1 = 40.7681   # Latitude of point 1
# lon2 = -118.2437  # Longitude of point 2
# lat2 = 34.0522   # Latitude of point 2

# distance = haversine(lon1, lat1, lon2, lat2)
# print(f"Distance: {distance:.2f} kilometers")

def get_dist_time(speed,lon1,lat1,lon2,lat2):

    point1 = (lon1, lat1)
    point2 = (lon2, lat2)
    
    # Преобразование метрических координат в градусы
    # Convert metrs system to gradus system for calculate dist
    utm_projection = Proj(init='epsg:2039')  
    if lon1 > 180 or lat1 > 180:
     lon1, lat1 = transform(utm_projection, Proj(init='epsg:4326'), point1[0], point1[1])
    if lon2 > 180 or lat2 > 180: 
     lon2, lat2 = transform(utm_projection, Proj(init='epsg:4326'), point2[0], point2[1])

    dist=  haversine(lon1, lat1, lon2, lat2)*1000
    time = dist/speed
    return dist,time

"""
def get_dist_time(speed,lon1,lat1,lon2,lat2):
    #dist=  haversine(lon1, lat1, lon2, lat2)*1000
    point1 = (lon1, lat1)
    point2 = (lon2, lat2)

    # Преобразование метрических координат в градусы
    # Convert metrs system to gradus system for calculate dist
    utm_projection = Proj(init='epsg:2039')  
    if lon1 > 180 or lat1 > 180:
     lon1, lat1 = transform(utm_projection, Proj(init='epsg:4326'), point1[0], point1[1])
    if lon2 > 180 or lat2 > 180: 
     lon2, lat2 = transform(utm_projection, Proj(init='epsg:4326'), point2[0], point2[1])

    # Расстояние между точками в метрах
    # Distance between points 
    #dist = distance((lat1, lon1), (lat2, lon2)).meters
    dist = haversine(lat1, lon1, lat2, lon2).meters
    
    #dist = distance(p1, p2).meters
    time=dist/speed
    return dist,time
"""
   







