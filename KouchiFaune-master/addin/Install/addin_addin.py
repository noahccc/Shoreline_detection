# -*- coding: utf-8 -*-

import arcpy
import pythonaddins

arcpy.env.overwriteOutput = True

class ButtonClass1(object):
    """Implementation for addin_addin.button_1 (Button)"""

    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        print "Choix d'un repertoire de travail, ainsi que l'image a classifier..."
        global wdPath
        wdPath = pythonaddins.OpenDialog("Selectionnez un repertoire de travail...", False, "C:", "Ajouter")
        print wdPath
        global rasterPath
        rasterPath = pythonaddins.OpenDialog("Selectionnez une couche matricielle...", False, "C:", "Ajouter")
        print rasterPath

        arcpy.MakeRasterLayer_management(rasterPath, "rasterLayer")

class ToolClass41(object):
    """Implementation for addin_addin.tool (Tool)"""
    def __init__(self):
        self.enabled = True
        self.cursor = 3
        self.shape = "Line" # Can set to "Line", "Circle" or "Rectangle" for interactive shape drawing and to activate the onLine/Polygon/Circle event sinks.

    def onLine(self, line_geometry):
        print "Creation du masque..."
        self.maskPart = line_geometry.getPart(0)
        coord = []
        for pt in self.maskPart:
            coord.append([pt.X, pt.Y])

        firstpoint = coord[0]
        coord.append(firstpoint)

        # Set local variables
        out_path = wdPath
        out_name = "maskRaster"
        geometry_type = "POLYGON"
        template = ""
        has_m = "DISABLED"
        has_z = "DISABLED"
        # Use Describe to get a SpatialReference object
        spatial_ref = arcpy.Describe(rasterPath).spatialReference
        # Execute CreateFeatureclass
        result = arcpy.CreateFeatureclass_management(out_path, out_name, geometry_type, template,
                                            has_m, has_z, spatial_ref)

        global mask_class
        mask_class = result[0]
        with arcpy.da.InsertCursor(mask_class, ['SHAPE@']) as cursor:
            cursor.insertRow([coord])

class ToolClass43(object):
    """Implementation for addin_addin.tool_2 (Tool)"""
    def __init__(self):
        self.enabled = True
        self.shape = "NONE" # Can set to "Line", "Circle" or "Rectangle" for interactive shape drawing and to activate the onLine/Polygon/Circle event sinks.
    def onClick(self):
        print "Execution du Extract by Mask..."
        # Set local variables
        inRaster = rasterPath
        inMaskData = mask_class

        # Execute ExtractByMask
        outExtractByMask = arcpy.sa.ExtractByMask(inRaster, inMaskData)
        arcpy.MakeRasterLayer_management(outExtractByMask, "extracted raster")

        # Dé-sélection des couches inutiles
        selectedLayers = ["maskRaster", "rasterLayer"]
        mxd = arcpy.mapping.MapDocument("current")
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        layers = arcpy.mapping.ListLayers(mxd, "*", df)

        for layer in layers:
            if layer.name in selectedLayers:
                layer.visible = False

        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()

class ComboBoxClass1(object):
    """Implementation for addin_addin.combobox (ComboBox)"""
    def __init__(self):
        self.items = ["Vegetation saine", "Vegetation fletrie", "Sable sec", "Sable humide", "Laisse de mer"]
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWWW'
    def onSelChange(self, selection):
        global selectedClass
        selectedClass = selection

class ToolClass48(object):
    """Implementation for addin_addin.tool (Tool)"""
    def __init__(self):
        self.enabled = True
        self.shape = "Line" # Can set to "Line", "Circle" or "Rectangle" for interactive shape drawing and to activate the onLine/Polygon/Circle event sinks.

    def onClick(self):
        layerNames = []
        for layer in arcpy.mapping.ListLayers(arcpy.mapping.MapDocument("CURRENT"), "", None):
            layerNames.append(layer.name)
        if "training_sites" in layerNames:
            print "La couche contenant les sites d'entrainement existe deja!"
        else:
            # Set local variables
            out_path = wdPath
            out_name = "training_sites"
            geometry_type = "POLYGON"
            template = ""
            has_m = "DISABLED"
            has_z = "DISABLED"
            # Use Describe to get a SpatialReference object
            spatial_ref = arcpy.Describe(rasterPath).spatialReference
            # Execute CreateFeatureclass
            self.result = arcpy.CreateFeatureclass_management(out_path, out_name, geometry_type, template,
                                                has_m, has_z, spatial_ref)
            arcpy.AddField_management("training_sites", "Classe", "TEXT")
            arcpy.AddField_management("training_sites", "aire", "DOUBLE")
            arcpy.AddField_management("training_sites", "pixels", "DOUBLE")

    def onLine(self, line_geometry):
        print "Creation du site d'entrainement..."
        self.site = line_geometry.getPart(0)
        coord = []
        for pt in self.site:
            coord.append([pt.X, pt.Y])

        firstpoint = coord[0]
        coord.append(firstpoint)

        # print "Coord avec premier point (pour fermer polygone) ", coord

        global trainingSitesDB
        trainingSitesDB = self.result[0]
        with arcpy.da.InsertCursor(trainingSitesDB, ['SHAPE@']) as cursor:
            cursor.insertRow([coord])
        with arcpy.da.UpdateCursor(trainingSitesDB, ["Classe"]) as cursor:
            for row in cursor:
                if row[0] == u' ':
                    # print "list is empty"
                    row[0] = selectedClass
                    cursor.updateRow(row)
                # print row

        # calcul de l'aire du polygone créé
        # with arcpy.da.UpdateCursor("training_sites", "aire") as pixels1:
        #     for i in pixels1:
        #         if i[0] == 0.0:
        #             arcpy.CalculateField_management("training_sites", "aire", "!shape.area!", "PYTHON")
        #
        # cellsize = arcpy.GetRasterProperties_management("extracted raster", "CELLSIZEX")
        # cellsize2 = float(str(cellsize).replace(',', '.'))
        # cellsizeEXP = cellsize2 ** 2
        # calculatecell = "!shape.area!/" + str(cellsizeEXP)
        # with arcpy.da.UpdateCursor("training_sites", "pixels") as pixels2:
        #     for i in pixels2:
        #         if i[0] == 0.0:
        #             arcpy.CalculateField_management("training_sites", "pixels", calculatecell, "PYTHON")
        #
        # with arcpy.da.UpdateCursor("training_sites", "pixels") as critere:
        #     for i in critere:
        #         if i[0] > 500:
        #             pythonaddins.MessageBox(
        #                 "Votre site d'entrainement dépasse la limite de 500 pixels!"
        #                 "Votre site mesurait " + ("%.0f" % (i[0])) + " pixels",
        #                 "Attention!", "0")
        #             critere.deleteRow()
        #         elif i[0] < 50:
        #             pythonaddins.MessageBox(
        #                 "Votre site d'entrainement est sous la limite de 50 pixels!"
        #                 "Votre site mesurait " + ("%.0f" % (i[0])) + " pixels",
        #                 "Attention!", "0")
        #             critere.deleteRow()

        arcpy.RefreshActiveView()

class ButtonClass4(object):
    """Implementation for addin_addin.button_4 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        print "Classification de la couche matricielle..."
        inRaster = "extracted raster"
        inSamples = "training_sites"
        outSig = wdPath+"\sig_file.gsg"
        sampField = "Classe"
        print "Classification du raster: ", inRaster
        print "Sites d'entrainement: ", inSamples
        print "Selon la classe: ", sampField
        print "Output du signatures file: ", outSig
        print "Creation du signature file (.gsg)..."
        arcpy.sa.CreateSignatures(inRaster, inSamples, outSig, "COVARIANCE", sampField)

        outRasterClassif = wdPath+"\MLClassif"

        # Set local variables
        inRaster = "extracted raster"
        sigFile = outSig
        probThreshold = "0.05"
        aPrioriWeight = "EQUAL"
        aPrioriFile = ""
        outConfidence = wdPath+"\confMLC"

        # Execute
        print "Execution de la classification par Maximum Likelihood..."
        mlcOut = arcpy.sa.MLClassify(inRaster, sigFile, probThreshold, aPrioriWeight, aPrioriFile, outConfidence)
        # Save the output
        mlcOut.save(outRasterClassif)
        # Add the classified raster to TOC and active view
        arcpy.MakeRasterLayer_management(outRasterClassif, "classified raster")

        Ref_TS_Classes = []
        global Ref_TS_Classes
        with arcpy.da.SearchCursor("classified raster", ["Value", "CLASSNAME"]) as RTC_cursor:
            for row in RTC_cursor:
                if row[1] != u'':
                    Ref_TS_Classes.append([row[0], row[1]])

class ButtonClass5(object):
    """Implementation for addin_addin.button_5 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        print "Nettoyage de la couche matricielle..."
        arcpy.Resample_management("classified raster", "resample", "0,3 0,3", "NEAREST")

        # Process: Boundary Clean
        arcpy.gp.BoundaryClean_sa("resample", "boundaryC", "NO_SORT", "TWO_WAY")

        # Process: Focal Statistics
        arcpy.gp.FocalStatistics_sa("boundaryC", "focalS", "Rectangle 6 6 CELL", "MAJORITY", "DATA")

        # Process: Focal Statistics (2)
        arcpy.gp.FocalStatistics_sa("focalS", "cleaned_raster", "Rectangle 6 6 CELL", "MAJORITY", "DATA")

        # Dé-sélection des couches inutiles
        selectedLayers = ["classified raster", "resample", "boundaryC", "focalS"]
        mxd = arcpy.mapping.MapDocument("current")
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        layers = arcpy.mapping.ListLayers(mxd, "*", df)

        for layer in layers:
            if layer.name in selectedLayers:
                layer.visible = False

        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()

class ButtonClass6(object):
    """Implementation for addin_addin.button_6 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        print "Vectorisation de la couche matricielle..."
        # Process: Raster to Polygon
        arcpy.RasterToPolygon_conversion("cleaned_raster", "vectorized_raster", "NO_SIMPLIFY", "Value")

        # Process: Simplify Polygon
        arcpy.SimplifyPolygon_cartography("vectorized_raster", "simplified_shoreline", "BEND_SIMPLIFY", "4 Meters",
                                          "10 SquareMeters", "NO_CHECK", "NO_KEEP")
        pythonaddins.MessageBox(
            "Vectorisation et simplification de la couche matricielle terminé!".decode('utf-8').encode('cp1252'),
            "Vectorisation", "0")

        real_classes_gc = [[1, u'Vegetation saine'], [2, u'Vegetation fletrie'], [3, u'Sable sec'], [4, u'Sable humide'], [5, u'Laisse de mer']]

        with arcpy.da.UpdateCursor("simplified_shoreline", "gridcode") as gcc_cursor:
            for row in gcc_cursor:
                if row[0] > 0:
                    for i in Ref_TS_Classes:
                        for j in real_classes_gc:
                            if row[0] == i[0]:
                                temp = i[1]
                                if j[1] == temp:
                                    row[0] = j[0]
                                    gcc_cursor.updateRow(row)
                else:
                    pass

class ButtonClass7(object):
    """Implementation for addin_addin.button_7 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        print "Extraction des intersections des polygones a l'aide d'un arbre de decision..."

        # Feature to line
        arcpy.FeatureToLine_management("simplified_shoreline", "polylines_shoreline", "0.001 Meters", "NO_ATTRIBUTES")

        # Create empty shape to store points
        # Set local variables
        out_path = wdPath
        out_name = "mid_points"
        geometry_type = "POINT"
        template = ""
        has_m = "DISABLED"
        has_z = "DISABLED"
        # Use Describe to get a SpatialReference object
        spatial_ref = arcpy.Describe("simplified_shoreline").spatialReference
        # Execute CreateFeatureclass
        arcpy.CreateFeatureclass_management(out_path, out_name, geometry_type, template, has_m, has_z,
                                                     spatial_ref)

        # Create points at the middle distance on every polyline in polylines_shoreline
        arcpy.DeleteFeatures_management("mid_points")

        with arcpy.da.SearchCursor("polylines_shoreline", "SHAPE@") as in_cursor, \
                arcpy.da.InsertCursor("mid_points", "SHAPE@") as out_cursor:
            for row in in_cursor:
                midpoint = row[0].positionAlongLine(0.50, True).firstPoint
                out_cursor.insertRow([midpoint])

        # Generate table of mid_points neighbors
        arcpy.GenerateNearTable_analysis("mid_points", "simplified_shoreline", "shoreline_neighbors", "0 Meters",
                                         "NO_LOCATION", "NO_ANGLE", "ALL", 2)

        arcpy.CalculateField_management("shoreline_neighbors", "IN_FID", "[IN_FID]+1", "VB")

        arcpy.JoinField_management("shoreline_neighbors", "NEAR_FID", "simplified_shoreline", "OBJECTID", "gridcode")

        arcpy.Statistics_analysis("shoreline_neighbors", "shoreline_neighbors_dissolved", [["gridcode", "FIRST"], ["gridcode", "LAST"]], "IN_FID")

        with arcpy.da.UpdateCursor("shoreline_neighbors_dissolved", ["FIRST_gridcode", "LAST_gridcode"]) as updateGC_cursor:
            temp = 0
            for row in updateGC_cursor:
                temp = row[0]
                if row[0] > row[1]:
                    row[0] = row[1]
                    row[1] = temp
                    updateGC_cursor.updateRow(row)
                else:
                    pass

        arcpy.AddField_management("shoreline_neighbors_dissolved", "intersection_type", "TEXT")
        arcpy.CalculateField_management("shoreline_neighbors_dissolved", "intersection_type", '[FIRST_gridcode] & " & " & [LAST_gridcode]', "VB")

        arcpy.JoinField_management("polylines_shoreline", "OBJECTID", "shoreline_neighbors_dissolved", "IN_FID", "intersection_type")

        with arcpy.da.UpdateCursor("polylines_shoreline", "intersection_type") as cleaningCursor:
            unwanted_types = ["1 & 1", "2 & 2", "3 & 3", "4 & 4", "5 & 5"]
            for row in cleaningCursor:
                if row[0] in unwanted_types:
                    cleaningCursor.deleteRow()

        arcpy.SelectLayerByAttribute_management("polylines_shoreline", "CLEAR_SELECTION")
        arcpy.SelectLayerByAttribute_management("polylines_shoreline", "NEW_SELECTION", "intersection_type = '1 & 5' OR intersection_type = '2 & 5'")
        arcpy.MakeFeatureLayer_management("polylines_shoreline", "Indicateurs forts")

        arcpy.SelectLayerByAttribute_management("polylines_shoreline", "CLEAR_SELECTION")
        arcpy.SelectLayerByAttribute_management("polylines_shoreline", "NEW_SELECTION",
                                                "intersection_type = '1 & 3' OR intersection_type = '1 & 4' OR intersection_type = '2 & 3' OR intersection_type = '2 & 4' OR intersection_type = '3 & 5' OR intersection_type = '4 & 5'")
        arcpy.MakeFeatureLayer_management("polylines_shoreline", "Indicateurs moyens")

        arcpy.SelectLayerByAttribute_management("polylines_shoreline", "CLEAR_SELECTION")
        arcpy.SelectLayerByAttribute_management("polylines_shoreline", "NEW_SELECTION",
                                                "intersection_type = '1 & 2' OR intersection_type = '3 & 4'")
        arcpy.MakeFeatureLayer_management("polylines_shoreline", "Indicateurs faibles")

        # Dé-sélection des couches inutiles
        selectedLayers = ["Indicateurs forts", "Indicateurs moyens", "Indicateurs faibles", "rasterLayer"]
        mxd = arcpy.mapping.MapDocument("current")
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
        layers = arcpy.mapping.ListLayers(mxd, "*", df)

        for layer in layers:
            layer.visible = False
        for layer1 in layers:
            if layer1.name in selectedLayers:
                layer1.visible = True

        arcpy.RefreshTOC()
        arcpy.RefreshActiveView()
