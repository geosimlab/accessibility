import math
from scipy.spatial import KDTree
from qgis.core import QgsWkbTypes
                      

class cls_footpath_on_air_b_b:
    def __init__(self, layer_origins, walk_dist = 300, layer_origins_field_id = "osm_id", speed = 1):
        self.layer_origins = layer_origins
        self.layer_origins_field_id = layer_origins_field_id
        self.features = list(self.layer_origins.getFeatures())
        self.walk_dist = walk_dist
        self.speed = speed

        points = []
        for feature in self.features:
            geom = feature.geometry()
            if geom.type() == QgsWkbTypes.PointGeometry:
                pt = geom.asPoint()
            elif geom.type() == QgsWkbTypes.PolygonGeometry:
                pt = geom.centroid().asPoint()
            else:
                multi_polygon = geom.asMultiPolygon()
                pt = multi_polygon[0]     

            points.append((pt.x(), pt.y()))
        
        self.kd_tree_buildings = KDTree(points)
    
    def get_nearby_buildings(self, id):
        
        target_feature = None
        for feature in self.features:
            if str(feature.attribute(self.layer_origins_field_id)) == str(id):
                target_feature = feature
                break

        geom = target_feature.geometry()
        if geom.type() == QgsWkbTypes.PointGeometry:
            target_feature_pt = geom.asPoint()
        elif geom.type() == QgsWkbTypes.PolygonGeometry:
            target_feature_pt = geom.centroid().asPoint()
        else:
            multi_polygon = geom.asMultiPolygon()
            target_feature_pt = multi_polygon[0]     

        target_point = (target_feature_pt.x(), target_feature_pt.y())

        nearest_features = []
        indices = self.kd_tree_buildings.query_ball_point(target_point, r=self.walk_dist)
        
        for index in indices:
            feature = self.features[index]
            feature_geom = feature.geometry().centroid().asPoint()
            distance = round(math.sqrt((feature_geom.x() - target_point[0]) ** 2 + (feature_geom.y() - target_point[1]) ** 2))
            nearest_features.append((int(feature.attribute(self.layer_origins_field_id)), round(distance/self.speed)))

        return nearest_features       
        
    