"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify *
*   it under the terms of the GNU General Public License as published by *
*   the Free Software Foundation; either version 2 of the License, or    *
*   (at your option) any later version.                                  *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsWkbTypes,
                       QgsFeature,
                       QgsGeometry)
from osgeo import ogr


class GeometryLinearizer(QgsProcessingAlgorithm):
    """
    Converts MultiCurve and MultiSurface geometries to linear equivalents.
    """

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    TOLERANCE = 'TOLERANCE'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GeometryLinearizer()

    def name(self):
        return 'geometrylinearizer'

    def displayName(self):
        return self.tr('Linearize Curved Geometries')

    def group(self):
        return self.tr('Geometry Tools')

    def groupId(self):
        return 'geometrytools'

    def shortHelpString(self):
        return self.tr("Converts curved geometries like MultiCurve and MultiSurface into linear equivalents using the Segmentize operation.")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOLERANCE,
                self.tr('Segmentize Tolerance'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=3.0
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        total = 100.0 / source.featureCount() if source.featureCount() else 0

        for current, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break

            geom = feature.geometry()
            if not geom:
                continue

            ogr_geom = ogr.CreateGeometryFromWkb(geom.asWkb())
            linear_geom = GeometryConverter.linearize_geometry(ogr_geom.Clone(), tolerance)

            if linear_geom is None:
                feedback.pushWarning(f"Skipping feature {feature.id()} - could not linearize geometry")
                continue

            new_feature = QgsFeature(feature)
            wkb = linear_geom.ExportToWkb()
            if not isinstance(wkb, bytes):
                wkb = bytes(wkb)
            geom_obj = QgsGeometry()
            geom_obj.fromWkb(wkb)
            new_feature.setGeometry(geom_obj)
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}


class GeometryConverter:
    @staticmethod
    def convert_multicurve_to_multilinestring(geom):
        multiline = ogr.Geometry(ogr.wkbMultiLineString)
        for i in range(geom.GetGeometryCount()):
            subgeom = geom.GetGeometryRef(i)
            linestring = GeometryConverter.linearize_geometry(subgeom)
            if linestring is not None:
                multiline.AddGeometry(linestring)
        return multiline

    @staticmethod
    def convert_multisurface_to_multipolygon(geom):
        multipoly = ogr.Geometry(ogr.wkbMultiPolygon)
        for i in range(geom.GetGeometryCount()):
            subgeom = geom.GetGeometryRef(i)
            polygon = GeometryConverter.linearize_geometry(subgeom)
            if polygon is not None:
                multipoly.AddGeometry(polygon)
        return multipoly

    @staticmethod
    def is_multicurve(geom):
        return (
            geom.GetGeometryType() == ogr.wkbMultiCurve or
            geom.GetGeometryType() == ogr.wkbMultiCurve + 1000 or
            geom.GetGeometryName().upper() == "MULTICURVE"
        )

    @staticmethod
    def is_multisurface(geom):
        return (
            geom.GetGeometryType() == ogr.wkbMultiSurface or
            geom.GetGeometryType() == ogr.wkbMultiSurface + 1000 or
            geom.GetGeometryName().upper() == "MULTISURFACE"
        )


    @staticmethod
    def linearize_geometry(geom, segmentize_tolerance):
        if geom is None:
            return None
        try:
            geom = geom.GetLinearGeometry() or geom
        except Exception:
            pass  # If segmentize fails, keep geometry as is 

        if GeometryConverter.is_multicurve(geom):
            geom = GeometryConverter.convert_multicurve_to_multilinestring(geom)
        elif GeometryConverter.is_multisurface(geom):
            geom = GeometryConverter.convert_multisurface_to_multipolygon(geom)
        
        curve_types = [
            ogr.wkbCircularString, ogr.wkbCompoundCurve, ogr.wkbCurvePolygon,
            ogr.wkbMultiCurve, ogr.wkbMultiSurface, ogr.wkbCurve, ogr.wkbCircularStringZ,
            ogr.wkbCompoundCurveZ, ogr.wkbCurvePolygonZ, ogr.wkbMultiCurveZ, ogr.wkbMultiSurfaceZ, ogr.wkbCurveZ
        ]
        if geom.GetGeometryType() in curve_types or "CURVE" in geom.GetGeometryName().upper():
            geom = geom.segmentize(segmentize_tolerance)
 
            linearized_subs = []
            for i in range(geom.GetGeometryCount()):
                sub = geom.GetGeometryRef(i)
                if sub is not None:
                    linear_sub = GeometryConverter.linearize_geometry(sub)
                    if linear_sub is not None:
                        linearized_subs.append(linear_sub)
            # Remove all sub-geometries and add back the linearized ones

            if linearized_subs:
                for _ in range(geom.GetGeometryCount()-1, -1, -1):
                    geom.RemoveGeometry(_)
                for linear_sub in linearized_subs:
                    geom.AddGeometry(linear_sub)

            geom = geom.GetLinearGeometry()
        return geom