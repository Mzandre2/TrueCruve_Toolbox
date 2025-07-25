## TrueCurve Toolbox

A cross-platform toolset for converting complex curved geometries (e.g., CircularString, CurvePolygon, MultiCurve, MultiSurface) into linear representations (LineString, Polygon, etc.), ensuring compatibility with a wide range of GIS software and workflows.

---
## **Supported Formats:**
  - File Geodatabase (.gdb)
  - GeoPackage (.gpkg)
  - Shapefile (.shp)
  - ESRI JSON (.json)
  - GeoJSON (.geojson)
  - DXF (.dxf)
  - DWG (.dwg) (limited support)

---

## Project Architecture

The toolbox is implemented as three interoperable modules:

- **Standalone Python Script** (`True_Curve.py`): Command-line and GUI modes for batch or interactive use.
- **ArcGIS Python Toolbox** (`ArcGIS_curves.pyt`): Integrates with ArcGIS Pro as a toolbox.
- **QGIS Processing Script** (`QGIS_Remove_curved_geometry.py`): Integrates with QGIS Processing Toolbox.

All modules share the same core logic: detecting, segmentizing, and linearizing curve-based geometries, preserving attributes and coordinate systems.

---

## Getting Started

### Prerequisites
- Python 3.x
- GDAL/OGR Python bindings (included in both ARC or QGIS)
- ArcGIS Pro (for ArcGIS toolbox)
- QGIS (for QGIS script)

### Installation & Usage

#### Standalone Script
- Place your input files in a readable directory (avoid special characters or spaces in path names).
- Ensure files are not open in other applications.

**Terminal (Batch Mode):**
```sh
python True_Curve.py --input <input_path> --output <output_path> --segmenting_tolerance <tolerance>
```
| Argument                | Required | Description                                                                                      |
|-------------------------|----------|--------------------------------------------------------------------------------------------------|
| `--input <input_path>`  | Yes      | Path to the input file or folder.                                                                |
| `--output <output_path>`| No       | Path for the output file or folder. If not provided, the output will be saved in the same directory as the input file. A suffix will be appended to the filename. |
| `--segmentizing_tolerance <tolerance>` | No | Tolerance for segmentizing curves. Default is 2m if not specified only applies if linearization fails.     |



**GUI Mode:**
```sh
python True_Curve.py -gui
```
Or double-click `Remove True Curves.vbs` to launch the GUI.

#### QGIS Version
- Copy `QGIS_Remove_curved_geometry.py` to your QGIS plugin or processing scripts folder.
- Restart QGIS if needed.
- Find the tool under Processing Toolbox → Geometry Tools → Linearize Curved Geometries.

#### ArcGIS Version
- Add `ArcGIS_curves.pyt` as a toolbox in ArcGIS Pro (Catalog pane → Add Toolbox).
- Run the tool, specifying input, output, and segmentize tolerance.

---

## Project Structure

- `True_Curve.py` — Standalone script
- `ArcGIS_curves.pyt` — ArcGIS Python toolbox
- `QGIS_Remove_curved_geometry.py` — QGIS processing script
- `Remove True Curves.vbs` — GUI launcher
- `tkdnd2/` — Drag-and-drop support for GUI
- Documentation and SOP files

---

## Key Features

- Detects and linearizes complex curved geometries
- Supports multiple GIS formats (GDB, GPKG, SHP, JSON, GeoJSON, DXF, DWG)
- Preserves attributes and coordinate systems
- Batch and interactive (GUI) modes
- Integrates with ArcGIS Pro and QGIS
- Customizable segmenting tolerance

---

> post_title: TrueCurve Toolbox

> categories: [GIS, Geometry Processing, Python, ArcGIS, QGIS]

> tags: [geometry, linearization, GIS, ArcGIS, QGIS, Python]

> ai_note: 'This README was generated with the help of AI.'

> post_date: 2025-07-25
---