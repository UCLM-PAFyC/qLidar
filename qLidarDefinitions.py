# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGIS plugin to integrate Point Clouds from LIDAR or Photogrammetry
        copyright            : (C) David Hernandez Lopez
        email                : david.hernandez@uclm.es
 ***************************************************************************/
"""

__author__ = 'david.hernandez@uclm.es'

CONST_AUTHOR_MAIL = 'david.hernandez@uclm.es'
CONST_SETTINGS_PLUGIN_NAME = "qLidar"
CONST_SETTINGS_FILE_NAME = "qLidar.ini"
CONST_PROGRAM_NAME = "qLidar:"
CONST_PROGRAM_TITLE = "qLidar"
CONST_NO_COMBO_SELECT = " ... "
CONST_GRID_SIZE_ACCURACY = 1
CONST_SELECT_ROIS_SHAPEFILES_DIALOG_TITLE = "Select ROIs Shapefiles"
CONST_DOCUMENTS_TYPE_SHAPEFILE = "shp"
CONST_TEMPLATE_PATH = "\\templates"
CONST_SYMBOLOGY_POINT_CLOUD_TEMPLATE = "\\qLidar.qml"
CONST_SYMBOLOGY_TILES_TEMPLATE = "\\Tiles.qml"
CONST_SYMBOLOGY_ROIS_TEMPLATE = "\\ROIs.qml"
CONST_SELECT_POINT_CLOUD_FILES_DIALOG_TITLE = "Select Point Cloud Files"
CONST_DOCUMENTS_TYPE_LASFILE = "las"
CONST_DOCUMENTS_TYPE_LAZFILE = "laz"
CONST_PROCESS_LIST_EDITION_DIALOG_TITLE = "Process List Edition"
CONST_RUN_PROCESS_LIST_DIALOG_TITLE = "Run Process List"
CONST_PROJECT_MANAGEMENT_TEMPORAL_PATH = "/temp"
CONST_PROJECT_MANAGEMENT_OUTPUT_PATH = "/output"

CONST_SPATIALITE_LAYERS_TILES_TABLE_NAME = "tiles"
CONST_SPATIALITE_LAYERS_TILES_TABLE_GEOMETRY_COLUMN = "the_geom"

CONST_SPATIALITE_LAYERS_TILE_TABLE_GEOMETRY_COLUMN = "the_geom"

CONST_SPATIALITE_LAYERS_ROIS_TABLE_NAME = "rois"
CONST_SPATIALITE_LAYERS_ROIS_TABLE_GEOMETRY_COLUMN = "the_geom"

CONST_LAYER_TREE_PROJECT_NAME = "Point Cloud 3D"
CONST_LAYER_TREE_PCTILES_NAME = "Point Cloud Tiles"

CONST_LAYER_PCTILES_FIELD_ID_NAME = "id"

CONST_RCM_REPORT_DEFAULT_SELECTED_CLASSES = "2;3;4;5;6;7"

CONST_POINTS_BY_MILIMETER = 0.5 # un punto cada dos milimetros de pantalla, a la escala
CONST_MAXIMUM_SCALE = 0.01 # 100:1
CONST_POINTCLOUDFILE_CLASS_NUMBER_REMOVE = 22 # LAS_1_4_r14.pdf, page 30

CONST_PROJECTS_STRING_SEPARATOR = "@#&"

CONST_POINTCLOUDFILE_PYTHON_TAG_POSITION      = "p"
CONST_POINTCLOUDFILE_PYTHON_TAG_IX            = "x"
CONST_POINTCLOUDFILE_PYTHON_TAG_IY            = "y"
CONST_POINTCLOUDFILE_PYTHON_TAG_Z             = "z"
CONST_POINTCLOUDFILE_PYTHON_TAG_GPS_TIME      = "gt"
CONST_POINTCLOUDFILE_PYTHON_TAG_CLASS         = "c"
CONST_POINTCLOUDFILE_PYTHON_TAG_CLASS_NEW     = "cn"
CONST_POINTCLOUDFILE_PYTHON_TAG_VALUES_8BITS  = "v8"
CONST_POINTCLOUDFILE_PYTHON_TAG_VALUES_16BITS = "v16"

CONST_POINTCLOUDFILE_PARAMETER_COLOR        = "Color"
CONST_POINTCLOUDFILE_PARAMETER_GPS_TIME     = "GpsTime"
CONST_POINTCLOUDFILE_PARAMETER_USER_DATA    = "UserData"
CONST_POINTCLOUDFILE_PARAMETER_INTENSITY    = "Intensity"
CONST_POINTCLOUDFILE_PARAMETER_SOURCE_ID    = "SourceId"
CONST_POINTCLOUDFILE_PARAMETER_NIR          = "Nir"
CONST_POINTCLOUDFILE_PARAMETER_RETURN       = "Return"
CONST_POINTCLOUDFILE_PARAMETER_RETURNS      = "Returns"
CONST_POINTCLOUDFILE_PARAMETER_COLOR_BYTES  = "ColorBytes"
CONST_POINTCLOUDFILE_PARAMETER_COLOR_RED    = "R"
CONST_POINTCLOUDFILE_PARAMETER_COLOR_GREEN  = "G"
CONST_POINTCLOUDFILE_PARAMETER_COLOR_BLUE   = "B"

CONST_MINIMUM_HEIGHT = -200
CONST_MAX_POINT_TILES = 80
CONST_TILE_NAME = "tile_name"
CONST_TILE_FIELD_NAME_FILE_ID = "file_id"
CONST_TILE_FIELD_NAME_POSITION = "pos"
CONST_TILE_FIELD_NAME_CLASS = "class"
CONST_TILE_FIELD_NAME_CLASS_NEW = "class_new"
CONST_TILE_FIELD_NAME_ALTITUDE = "altitude"
CONST_TILE_FIELD_NAME_REMOVED = "removed"
CONST_TILE_FIELD_NAME_GPS_TIME = "gps_time"
CONST_TILE_FIELD_NAME_USER_DATA = "user_data"
CONST_TILE_FIELD_NAME_RETURN = "return"
CONST_TILE_FIELD_NAME_RETURNS = "returns"
CONST_TILE_FIELD_NAME_INTENSITY = "intensity"
CONST_TILE_FIELD_NAME_SOURCE_ID = "source_id"
CONST_TILE_FIELD_NAME_NIR = "nir"

CONST_ACTION_ALL_CLASSES_VALUE = 255
CONST_ACTION_CHANGE_CLASS = "ChangeClass"
CONST_ACTION_RECOVER_ORIGINAL_CLASS = "RecoverOriginalClass"
CONST_ACTION_DELETE = "Delete"
CONST_ACTION_RECOVER_DELETED = "RecoverDeleted"
CONST_ACTION_SELECT_ONLY = "SelectOnly"
CONST_ACTION_UNSELECT = "Unselect"
# CONST_ACTION_ = ""

CONST_PROCESSING_TOOLS_RUN_BUTTON_PROCESS_LIST_TEXT = "Run Process List"
CONST_PROCESSING_TOOLS_RUN_BUTTON_PROCESS_TEXT = "Run Process"

CONST_EGM08_25_FILE_NAME = "egm08_25.gtx"
CONST_EGM08_25_COMPRESS_FILE_NAME = "egm08_25.7z"
