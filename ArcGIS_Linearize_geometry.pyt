import os
import pathlib
from osgeo import ogr, gdal
import arcpy

gdal.PushErrorHandler('CPLQuietErrorHandler')
ogr.UseExceptions()

class Toolbox(object):
    def __init__(self):
        self.label = "Geometry Linearizer Toolbox"
        self.alias = "geometry_linearizer"
        self.tools = [LinearizeGeometryToolClass, LinearizeGeometryToolLayer]

class LinearizeGeometryToolClass(object):
    def __init__(self):
        self.label = "Linearize Curved Geometries - Feature Class"
        self.description = "Converts MultiCurve and MultiSurface geometries into linear equivalents using OGR's Segmentize."

    def getParameterInfo(self):
        return [
            arcpy.Parameter(
                displayName="Input Feature Class",
                name="in_ds",
                datatype="DEFeatureClass",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Output Feature Class",
                name="out_ds",
                datatype="DEFeatureClass",
                parameterType="Required",
                direction="Output"
            ),
            arcpy.Parameter(
                displayName="Segmentize Tolerance",
                name="tolerance",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input"
            )
        ]

    def isLicensed(self):
        return True

    def execute(self, parameters, messages):
        in_ds = parameters[0].valueAsText
        out_ds = parameters[1].valueAsText
        tolerance = float(parameters[2].value)

        messages.addMessage(f"out_ds: {out_ds}")

        # Use arcpy to check and delete existing output
        messages.addMessage(f"Checking if output exists with arcpy: {arcpy.Exists(out_ds)}")
        if arcpy.Exists(out_ds):
            messages.addMessage(f"Deleting existing output dataset with arcpy: {out_ds}")
            arcpy.Delete_management(out_ds)

        # Describe input to get geometry type and spatial reference
        desc = arcpy.Describe(in_ds)
        geometry_type = desc.shapeType
        spatial_ref = desc.spatialReference

        # Create output feature class
        messages.addMessage(f"Creating output feature class: {out_ds}")
        arcpy.CreateFeatureclass_management(
            out_path=os.path.dirname(out_ds),
            out_name=os.path.basename(out_ds),
            geometry_type=geometry_type,
            spatial_reference=spatial_ref
        )

        # Copy fields from input to output, stripping table prefixes from field names
        input_fields = [f.name for f in arcpy.ListFields(in_ds) if f.type not in ("OID", "Geometry")]
        field_map = {}
        for f in arcpy.ListFields(in_ds):
            if f.type not in ("OID", "Geometry"):
                # Remove table prefix if present
                base_field = f.name.split(".")[-1]
                # Ensure field name is <= 64 chars and unique
                base_field = base_field[:64]
                orig_base_field = base_field
                i = 1
                while base_field in field_map.values():
                    base_field = f"{orig_base_field}_{i}"
                    base_field = base_field[:64]
                    i += 1
                field_map[f.name] = base_field
                arcpy.AddField_management(out_ds, base_field, f.type)

        # Use the mapped field names for input/output
        input_fields_out = [field_map[f] for f in input_fields]

        # Read and process features
        with arcpy.da.SearchCursor(in_ds, ["SHAPE@"] + input_fields) as in_cursor, \
             arcpy.da.InsertCursor(out_ds, ["SHAPE@"] + input_fields_out) as out_cursor:
            for row in in_cursor:
                shape = row[0]
                # Convert arcpy geometry to WKB for OGR
                ogr_geom = ogr.CreateGeometryFromWkb(shape.WKB)
                linear_geom = GeometryConverter.linearize_geometry(ogr_geom.Clone(), tolerance)
                if not linear_geom:
                    messages.addWarningMessage("Skipping feature — geometry couldn't be linearized.")
                    continue
                # Convert back to arcpy geometry
                new_shape = arcpy.FromWKB(linear_geom.ExportToWkb(), spatial_ref)
                out_cursor.insertRow((new_shape,) + row[1:])

        messages.addMessage("Geometry linearization completed.")


class LinearizeGeometryToolLayer(object):
    def __init__(self):
        self.label = "Linearize Curved Geometries - Feature Layer"
        self.description = "Converts MultiCurve and MultiSurface geometries into linear equivalents using OGR's Segmentize."

    def getParameterInfo(self):
        return [
            arcpy.Parameter(
                displayName="Input Feature Layer",
                name="in_ds",
                datatype="Feature Layer",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Output Feature Layer",
                name="out_ds",
                datatype="Feature Layer",
                parameterType="Required",
                direction="Output"
            ),
            arcpy.Parameter(
                displayName="Segmentize Tolerance",
                name="tolerance",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input"
            )
        ]

    def isLicensed(self):
        return True

    def execute(self, parameters, messages):
        in_ds = parameters[0].valueAsText
        out_ds = parameters[1].valueAsText
        tolerance = float(parameters[2].value)

        messages.addMessage(f"out_ds: {out_ds}")

        # Use arcpy to check and delete existing output
        messages.addMessage(f"Checking if output exists with arcpy: {arcpy.Exists(out_ds)}")
        if arcpy.Exists(out_ds):
            messages.addMessage(f"Deleting existing output dataset with arcpy: {out_ds}")
            arcpy.Delete_management(out_ds)

        # Describe input to get geometry type and spatial reference
        desc = arcpy.Describe(in_ds)
        geometry_type = desc.shapeType
        spatial_ref = desc.spatialReference

        # Create output feature class
        messages.addMessage(f"Creating output feature class: {out_ds}")
        arcpy.CreateFeatureclass_management(
            out_path=os.path.dirname(out_ds),
            out_name=os.path.basename(out_ds),
            geometry_type=geometry_type,
            spatial_reference=spatial_ref
        )

        # Copy fields from input to output
        input_fields = [f.name for f in arcpy.ListFields(in_ds) if f.type not in ("OID", "Geometry")]
        for field in input_fields:
            arcpy.AddField_management(out_ds, field, [f for f in arcpy.ListFields(in_ds) if f.name == field][0].type)

        # Read and process features
        with arcpy.da.SearchCursor(in_ds, ["SHAPE@"] + input_fields) as in_cursor, \
             arcpy.da.InsertCursor(out_ds, ["SHAPE@"] + input_fields) as out_cursor:
            for row in in_cursor:
                shape = row[0]
                # Convert arcpy geometry to WKB for OGR
                ogr_geom = ogr.CreateGeometryFromWkb(shape.WKB)
                linear_geom = GeometryConverter.linearize_geometry(ogr_geom.Clone(), tolerance)
                if not linear_geom:
                    messages.addWarningMessage("Skipping feature — geometry couldn't be linearized.")
                    continue
                # Convert back to arcpy geometry
                new_shape = arcpy.FromWKB(linear_geom.ExportToWkb(), spatial_ref)
                out_cursor.insertRow((new_shape,) + row[1:])

        messages.addMessage("Geometry linearization completed.")

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