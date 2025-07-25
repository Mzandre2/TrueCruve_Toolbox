' run_linearize.vbs
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat"" ""\\inpyosegis\Yosemite_EGIS\GIS_Workspace\GIS_Requests\2025\0701_Andre_TrueCruve_Toolbox\Linearize_geometry.py"" -gui", 0