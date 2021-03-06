# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGIS plugin to use Point Clouds from LIDAR or Photogrammetry
        copyright            : (C) David Hernandez Lopez
        email                : david.hernandez@uclm.es
 ***************************************************************************/
"""

# esto es un comentario

# dhl
import sys,os
from math import sqrt,ceil
import bisect
from osgeo import osr
from decimal import Decimal
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, QDir, QObject
from PyQt5.QtWidgets import QMessageBox,QFileDialog,QTabWidget,QInputDialog,QLineEdit
from qgis.core import QgsApplication, QgsDataSourceUri, QgsCoordinateReferenceSystem
# pluginsPath = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path()
# pluginPath = os.path.dirname(os.path.realpath(__file__))
# pluginPath = os.path.join(pluginsPath, pluginPath)
# libCppPath = os.path.join(pluginPath, 'libCpp')
# existsPluginPath = QDir(libCppPath).exists()
# sys.path.append(pluginPath)
# sys.path.append(libCppPath)
# os.environ["PATH"] += os.pathsep + libCppPath
# from libCpp.libPyPointCloudTools import IPyPCTProject
# from multipleFileSelectorDialog.multiple_file_selector_dialog import * #panel nueva camara
# from processListEditionDialog.process_list_edition_dialog import *
# import PCTDefinitions

from .qLidar_about_qdialog import AboutQDialog
from .multipleFileSelectorDialog.multiple_file_selector_dialog import *
from .processListEditionDialog.process_list_edition_dialog import *
from . import qLidarDefinitions
#  dhl

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal,QSettings, Qt
from PyQt5.QtWidgets import QTextEdit,QPushButton,QVBoxLayout, QProgressDialog

from math import floor
import re

from .selectionMapTools.rectangle_map_tool import RectangleMapTool
from .selectionMapTools.polygon_map_tool import PolygonMapTool
from .selectionMapTools.freehand_map_tool import FreehandMapTool

from qgis.core import Qgis
qgis_version_number_str = Qgis.QGIS_VERSION.split('-')[0]
qgis_version_first_number = int(qgis_version_number_str.split('.')[0])
qgis_version_second_number = int(qgis_version_number_str.split('.')[1])
qgis_version_third_number = int(qgis_version_number_str.split('.')[2])
qgis_version_second_number_change_buffer_parameters = 20

from osgeo import osr
projVersionMajor = osr.GetPROJVersionMajor()

FORM_CLASS = None

if projVersionMajor < 8:
    FORM_CLASS, _ = uic.loadUiType(os.path.join(
        os.path.dirname(__file__), 'qLidar_dockwidget_base_old_osgeo.ui'))
else:
    FORM_CLASS, _ = uic.loadUiType(os.path.join(
        os.path.dirname(__file__), 'qLidar_dockwidget_base.ui'))

class TextEditDialog(QDialog):
    def __init__(self, parent=None):
        super(TextEditDialog, self).__init__(parent)
        # Create widgets
        self.setWindowTitle("Edit value")
        self.qTextEdit = QTextEdit()
        self.setMinimumSize(QSize(440, 240))
        #self.button = QPushButton("Show Greetings")
        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.qTextEdit)
        self.acceptButton = QPushButton()
        self.acceptButton.setText("Accept")
        self.acceptButton.setMaximumWidth(80)
        layout.addWidget(self.acceptButton,0,Qt.AlignRight)
        self.acceptButton.clicked.connect(self.dialogAccept)
        #layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)
        self.accepted = False
        # Add button signal to greetings slot
        #self.button.clicked.connect(self.greetings)
    # Greets the user

    def dialogAccept(self):
        self.accepted = True
        self.accept()

    def setValue(self,value):
        self.qTextEdit.setText(value)

    def getValue(self):
        value = None
        if self.accepted:
            value = self.qTextEdit.toPlainText()
        return value

class qLidarDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self,
                 iface,
                 projVersionMajor,
                 pluginPath,
                 libCppPath,
                 currentPluginName,
                 settings,
                 iPyProject,
                 connectionFileName,#WithoutPath,
                 # modelManagementFileName,
                 parent=None):
        """Constructor."""
        super(qLidarDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setWindowTitle(qLidarDefinitions.CONST_PROGRAM_NAME)
        self.iface = iface
        self.projVersionMajor = projVersionMajor
        self.path_plugin = pluginPath
        self.path_libCpp = libCppPath
        self.current_plugin_name = currentPluginName
        self.settings = settings
        self.iPyProject = iPyProject
        self.isqLidarPlugin = False
        if self.current_plugin_name == qLidarDefinitions.CONST_SETTINGS_PLUGIN_NAME:
            self.isqLidarPlugin = True
        self.setupUi(self)
        self.connectionFileName = connectionFileName
        # self.modelManagementFileName= modelManagementFileName
        self.initialize()

    def actionSetVisiblePoints(self):
        for tileTableName in self.loadedTiles:
            layerList = QgsProject.instance().mapLayersByName(tileTableName)
            if len(layerList) == 1:
                vlayer = layerList[0]
                # ltv = self.iface.layerTreeView()
                # ltm_bis = ltv.model()
                root = QgsProject.instance().layerTreeRoot()
                ltm = QgsLayerTreeModel(root)
                # ltm = self.iface.layerTreeView().model() # old
                lsi = vlayer.renderer().legendSymbolItems()
                for classNumber in self.lavelSimbolByClassNumber:
                    className = self.lavelSimbolByClassNumber[classNumber]
                    ruleKey = [l.ruleKey() for l in lsi if l.label() == className]
                    # if ruleKey:
                    if not classNumber in self.visibleCheckBoxByClassNumber: # por la clase 8
                        continue
                    checkBox = self.visibleCheckBoxByClassNumber[classNumber]
                    if checkBox.isChecked():
                        ltm.findLegendNode(vlayer.id(), ruleKey[0]).setData(Qt.Checked, Qt.CheckStateRole)
                    else:
                        ltm.findLegendNode(vlayer.id(), ruleKey[0]).setData(Qt.Unchecked, Qt.CheckStateRole)
                self.iface.layerTreeView().refreshLayerSymbology(vlayer.id())
        return

    def actionWithSelectedPoints(self,classValue):
        selectedPoints,selectedTileNames = self.getSelectedPoints() # tile_name,fileId,pos, quito: classNew,class
        # [selectedPointsIdByTableName,numberOfSelectedPoints] = self.getSelectedPointsIdByTableName()
        if len(selectedPoints) == 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select at least one point")
            msgBox.exec_()
            return
        if self.selectOnlyRadioButton.isChecked()\
                or self.unselectRadioButton.isChecked():
            for selectedTileName in selectedTileNames:
                layers = QgsProject.instance().mapLayersByName(selectedTileName)
                if len(layers) != 1:
                    continue
                layer = layers[0]
                if layer.type() != QgsMapLayer.VectorLayer:
                    continue
                features = layer.selectedFeatures()
                for feature in features:
                    pointClassNew = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW]
                    if self.selectOnlyRadioButton.isChecked():
                        if pointClassNew != classValue \
                                and classValue != qLidarDefinitions.CONST_ACTION_ALL_CLASSES_VALUE:
                            layer.deselect(feature.id())
                    elif self.unselectRadioButton.isChecked():
                        if pointClassNew == classValue:
                            layer.deselect(feature.id())
            return
        if self.lockedClass0CheckBox.isChecked():
            self.lockedClasses[0] = True
        else:
            self.lockedClasses[0] = False
        if self.lockedClass1CheckBox.isChecked():
            self.lockedClasses[1] = True
        else:
            self.lockedClasses[1] = False
        if self.lockedClass2CheckBox.isChecked():
            self.lockedClasses[2] = True
        else:
            self.lockedClasses[2] = False
        if self.lockedClass3CheckBox.isChecked():
            self.lockedClasses[3] = True
        else:
            self.lockedClasses[3] = False
        if self.lockedClass4CheckBox.isChecked():
            self.lockedClasses[4] = True
        else:
            self.lockedClasses[4] = False
        if self.lockedClass5CheckBox.isChecked():
            self.lockedClasses[5] = True
        else:
            self.lockedClasses[5] = False
        if self.lockedClass6CheckBox.isChecked():
            self.lockedClasses[6] = True
        else:
            self.lockedClasses[6] = False
        if self.lockedClass7CheckBox.isChecked():
            self.lockedClasses[7] = True
        else:
            self.lockedClasses[7] = False
        # if self.lockedClass8CheckBox.isChecked():
        #     self.lockedClasses[8] = True
        # else:
        #     self.lockedClasses[8] = False
        if self.lockedClass9CheckBox.isChecked():
            self.lockedClasses[9] = True
        else:
            self.lockedClasses[9] = False
        # if self.lockedClass10CheckBox.isChecked():
        #     self.lockedClasses[10] = True
        # else:
        #     self.lockedClasses[10] = False
        # if self.lockedClass11CheckBox.isChecked():
        #     self.lockedClasses[11] = True
        # else:
        #     self.lockedClasses[11] = False
        # if self.lockedClass12CheckBox.isChecked():
        #     self.lockedClasses[12] = True
        # else:
        #     self.lockedClasses[12] = False
        # if self.lockedClass13CheckBox.isChecked():
        #     self.lockedClasses[13] = True
        # else:
        #     self.lockedClasses[13] = False

        strAction = ""
        if self.changeClassRadioButton.isChecked():
            strAction = qLidarDefinitions.CONST_ACTION_CHANGE_CLASS
        elif self.removeRadioButton.isChecked():
            strAction = qLidarDefinitions.CONST_ACTION_DELETE
        elif self.recoverRadioButton.isChecked():
            strAction = qLidarDefinitions.CONST_ACTION_RECOVER_DELETED
        elif self.toOriginalClassRadioButton.isChecked():
            strAction = qLidarDefinitions.CONST_ACTION_RECOVER_ORIGINAL_CLASS
        ret = self.iPyProject.pctUpdatePoints(self.projectPath,
                                              strAction,
                                              selectedPoints,
                                              classValue,
                                              self.lockedClasses)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n" + ret[1])
            msgBox.exec_()
            # self.projectsComboBox.setCurrentIndex(0)
            return
        for selectedTileName in selectedTileNames:
            layers = QgsProject.instance().mapLayersByName(selectedTileName)
            if len(layers) != 1:
                continue
            layer = layers[0]
            if layer.type() != QgsMapLayer.VectorLayer:
                continue
            layerInEdition = False
            features = layer.selectedFeatures()
            existsChanges = False
            for feature in features:
                pointClassNew = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW]
                featureChanges = False
                if pointClassNew in self.lockedClasses:
                    if self.lockedClasses[pointClassNew]:
                        continue
                if strAction == qLidarDefinitions.CONST_ACTION_CHANGE_CLASS:
                    if pointClassNew == qLidarDefinitions.CONST_POINTCLOUDFILE_CLASS_NUMBER_REMOVE:
                        continue
                    if pointClassNew == classValue:
                        continue
                    featureChanges = True
                    feature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW, classValue)
                elif strAction == qLidarDefinitions.CONST_ACTION_RECOVER_ORIGINAL_CLASS:
                    if pointClassNew == qLidarDefinitions.CONST_POINTCLOUDFILE_CLASS_NUMBER_REMOVE:
                        continue
                    if classValue != qLidarDefinitions.CONST_ACTION_ALL_CLASSES_VALUE:
                        if pointClassNew != classValue:
                            continue
                    pointClass = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS]
                    if pointClassNew == pointClass:
                        continue
                    featureChanges = True
                    feature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW,pointClass)
                elif strAction == qLidarDefinitions.CONST_ACTION_DELETE:
                    if pointClassNew == qLidarDefinitions.CONST_POINTCLOUDFILE_CLASS_NUMBER_REMOVE:
                        continue
                    if classValue != qLidarDefinitions.CONST_ACTION_ALL_CLASSES_VALUE:
                        if pointClassNew != classValue:
                            continue
                    featureChanges = True
                    feature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW,
                                         qLidarDefinitions.CONST_POINTCLOUDFILE_CLASS_NUMBER_REMOVE)
                elif strAction == qLidarDefinitions.CONST_ACTION_RECOVER_DELETED:
                    if pointClassNew != qLidarDefinitions.CONST_POINTCLOUDFILE_CLASS_NUMBER_REMOVE:
                        continue
                    pointClass = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS]
                    if classValue != qLidarDefinitions.CONST_ACTION_ALL_CLASSES_VALUE:
                        if pointClass != classValue:
                            continue
                    featureChanges = True
                    feature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW,pointClass)
                if featureChanges:
                    if not existsChanges:
                        existsChanges = True
                    if not layerInEdition:
                        layer.startEditing()
                        layerInEdition = True
                    layer.updateFeature(feature)
            if existsChanges:
                layer.commitChanges()
                layer.triggerRepaint()
        return

    def addProcessToList(self):
        crs = self.ppToolsIPCFsQgsProjectionSelectionWidget.crs()
        isValidCrs = crs.isValid()
        crsAuthId = crs.authid()
        if not "EPSG:" in crsAuthId:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not EPSG")
            msgBox.exec_()
            return
        crsEpsgCode = int(crsAuthId.replace('EPSG:',''))
        crsOsr = osr.SpatialReference()  # define test1
        if crsOsr.ImportFromEPSG(crsEpsgCode) != 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error importing OSR CRS from EPSG code" + str(crsEpsgCode))
            msgBox.exec_()
            return
        if not crsOsr.IsProjected():
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not a projected CRS")
            msgBox.exec_()
            return
        altitudeIsMsl = True
        verticalCrsEpsgCode = -1
        if self.projVersionMajor < 8:
            if self.ppToolsIPCFsAltitudeEllipsoidRadioButton.isChecked():
                altitudeIsMsl = False
        else:
            verticalCrsStr = self.ppToolsIPCFsVerticalCRSsComboBox.currentText()
            if not verticalCrsStr == qLidarDefinitions.CONST_ELLIPSOID_HEIGHT:
                verticalCrsEpsgCode = int(verticalCrsStr.replace('EPSG:',''))
        inputFiles = self.postprocessingIPCFs
        if len(inputFiles ) == 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select input files")
            msgBox.exec_()
            return
        outputFile = self.ppToolsOPCFsOutputFileLineEdit.text()
        outputPath = self.ppToolsOPCFsOutputPathLineEdit.text()
        suffixOutputFiles = self.ppToolsOPCFsSuffixLineEdit.text()
        prefixOutputFiles = self.ppToolsOPCFsPrefixLineEdit.text()
        # ??se puede ignorar para algunos procesos si hay varios ficheros de entrada? lasmerge ...
        # tengo que definir en un contenedor aquellos comandos que lo permiten
        if len(inputFiles ) > 1 and outputFile:
            if self.ppToolsOPCFsOutputPathPushButton.isEnabled():
                if not outputPath and not suffixOutputFiles:
                    msgBox = QMessageBox(self)
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setWindowTitle(self.windowTitle)
                    msgBox.setText("Select output path or suffix for several input files")
                    msgBox.exec_()
                    return
        if not outputFile and not outputPath and not suffixOutputFiles:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select output file, output path or suffix")
            msgBox.exec_()
            return
        command = None
        if self.ppToolsTabWidget.currentIndex() == 0: # Lastools command
            if not self.lastoolsPath:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Select Lastools path")
                msgBox.exec_()
                return
            command = self.ppToolsLastoolsCommandComboBox.currentText()
            if command == qLidarDefinitions.CONST_NO_COMBO_SELECT:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Select Lastools command")
                msgBox.exec_()
                return
        # elif self.ppToolsTabWidget.currentIndex() == 1:
        #     command = self.ppToolsInternalCommandComboBox.currentText()
        #     if command == qLidarDefinitions.CONST_NO_COMBO_SELECT:
        #         msgBox = QMessageBox(self)
        #         msgBox.setIcon(QMessageBox.Information)
        #         msgBox.setWindowTitle(self.windowTitle)
        #         msgBox.setText("Select Lastools command")
        #         msgBox.exec_()
        #         return
        if not command:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Command is None")
            msgBox.exec_()
            return
        if self.ppToolsTabWidget.currentIndex() == 0: # Lastools command
            ret = self.iPyProject.pctGetLastoolsCommandStrings(command,
                                                               inputFiles,
                                                               outputPath,
                                                               outputFile,
                                                               suffixOutputFiles,
                                                               prefixOutputFiles)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n" + ret[1])
                msgBox.exec_()
                return
            cont = 0
            for process in ret:
                if cont > 0:
                    self.processList.append(ret[cont])
                cont = cont + 1
            # strValue = ""
            # cont = 0
            # for values in ret:
            #     if cont > 0:
            #         strValue += ret[cont]
            #         strValue += "\n"
            #     cont = cont + 1
            # dialog = TextEditDialog()
            # dialog.setValue(strValue)
            # dialog.exec_()
            # text = dialog.getValue()
        # elif self.ppToolsTabWidget.currentIndex() == 1:
        #     ret = self.iPyProject.pctpctProcessInternalCommand(command,
        #                                                        inputFiles,
        #                                                        outputPath,
        #                                                        outputFile,
        #                                                        suffixOutputFiles,
        #                                                        prefixOutputFiles)
        #     if ret[0] == "False":
        #         msgBox = QMessageBox(self)
        #         msgBox.setIcon(QMessageBox.Information)
        #         msgBox.setWindowTitle(self.windowTitle)
        #         msgBox.setText("Error:\n" + ret[1])
        #         msgBox.exec_()
        #         return
        return

    def addProject(self):
        oldProjectPath=self.projectPathLineEdit.text()
        title="Select Project Path"
        strDir = QFileDialog.getExistingDirectory(self,title,self.path,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if strDir:
            if not strDir in self.projects:
                self.projects.append(strDir)
                self.projectsComboBox.addItem(strDir)
                strProjects = ""
                cont = 0
                for project in self.projects:
                    if cont > 0:
                        strProjects = strProjects + qLidarDefinitions.CONST_PROJECTS_STRING_SEPARATOR
                    strProjects += project
                    cont = cont + 1
                self.settings.setValue("projects", strProjects)
                self.settings.sync()
            pos = self.projectsComboBox.findText(strDir)
            if pos >= 0:
                self.projectsComboBox.setCurrentIndex(pos)
            self.path = strDir
            self.projectPathLineEdit.setText(strDir)
            self.settings.setValue("last_path", self.path)
            self.settings.sync()
        return

    def addPointCloudFiles(self):
        crs = self.addPCFsQgsProjectionSelectionWidget.crs()
        isValidCrs = crs.isValid()
        crsAuthId = crs.authid()
        if not "EPSG:" in crsAuthId:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not EPSG")
            msgBox.exec_()
            return
        crsEpsgCode = int(crsAuthId.replace('EPSG:',''))
        crsOsr = osr.SpatialReference()  # define test1
        if crsOsr.ImportFromEPSG(crsEpsgCode) != 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error importing OSR CRS from EPSG code" + str(crsEpsgCode))
            msgBox.exec_()
            return
        if not crsOsr.IsProjected():
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not a projected CRS")
            msgBox.exec_()
            return

        altitudeIsMsl = True
        verticalCrsEpsgCode = -1
        if self.projVersionMajor < 8:
            if self.addPCFsAltitudeEllipsoidRadioButton.isChecked():
                altitudeIsMsl = False
        else:
            verticalCrsStr = self.addPCFsVerticalCRSsComboBox.currentText()
            if not verticalCrsStr == qLidarDefinitions.CONST_ELLIPSOID_HEIGHT:
                verticalCrsEpsgCode = int(verticalCrsStr.replace('EPSG:',''))

        # projectPath=self.projectsComboBox.currentText()
        # if projectPath == qLidarDefinitions.CONST_NO_COMBO_SELECT:
        #     msgBox = QMessageBox(self)
        #     msgBox.setIcon(QMessageBox.Information)
        #     msgBox.setWindowTitle(self.windowTitle)
        #     msgBox.setText("Select project to remove from list")
        #     msgBox.exec_()
        #     return
        strPointCloudFiles = ''
        cont = 0
        for pointCloudFile in self.pointCloudFiles:
            if cont > 0:
                strPointCloudFiles = strPointCloudFiles + self.parametersFromPythonStringSeparator
            strPointCloudFiles = strPointCloudFiles + pointCloudFile
            cont = cont + 1
        initialDateTime = QDateTime.currentDateTime()
        if self.projVersionMajor < 8:
            ret = self.iPyProject.pctAddPointCloudFilesToProject(self.projectPath,
                                                                 crsEpsgCode,
                                                                 altitudeIsMsl,
                                                                 strPointCloudFiles)
        else:
            ret = self.iPyProject.pctAddPointCloudFilesToProject(self.projectPath,
                                                                 crsEpsgCode,
                                                                 verticalCrsEpsgCode,
                                                                 strPointCloudFiles)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
        else:
            finalDateTime = QDateTime.currentDateTime()
            initialSeconds = initialDateTime.toTime_t()
            finalSeconds = finalDateTime.toTime_t()
            totalDurationSeconds = finalSeconds - initialSeconds
            durationDays = floor(totalDurationSeconds / 60.0 / 60.0 / 24.0)
            durationHours = floor((totalDurationSeconds - durationDays * 60.0 * 60.0 * 24.0) / 60.0 / 60.0)
            durationMinutes = floor((totalDurationSeconds - durationDays * 60.0 * 60.0 * 24.0 - durationHours * 60.0 * 60.0) / 60.0)
            durationSeconds = totalDurationSeconds - durationDays * 60.0 * 60.0 * 24.0 - durationHours * 60.0 * 60.0 - durationMinutes * 60.0
            msgTtime = "- Process time:\n"
            msgTtime += "  - Start time of the process ......................: "
            msgTtime += initialDateTime.toString("yyyy/MM/dd - hh/mm/ss.zzz")
            msgTtime += "\n"
            msgTtime += "  - End time of the process ........................: "
            msgTtime += finalDateTime.toString("yyyy/MM/dd - hh/mm/ss.zzz")
            msgTtime += "\n"
            msgTtime += "  - Number of total seconds ........................: "
            msgTtime += f"{totalDurationSeconds:.3f}" # QString.number(totalDurationSeconds, 'f', 3)
            msgTtime += "\n"
            msgTtime += "    - Number of days ...............................: "
            msgTtime += str(durationDays) # QString.number(durationDays)
            msgTtime += "\n"
            msgTtime += "    - Number of hours ..............................: "
            msgTtime += str(durationHours) # QString.number(durationHours)
            msgTtime += "\n"
            msgTtime += "    - Number of minutes ............................: "
            msgTtime += str(durationMinutes) # QString.number(durationMinutes)
            msgTtime += "\n"
            msgTtime += "    - Number of seconds ............................: "
            msgTtime += f"{durationSeconds:.3f}" # QString.number(durationSeconds, 'f', 3)
            msgTtime += "\n"
            msg = "Process completed successfully"
            msg += "\n"
            msg += msgTtime
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText(msg)
            msgBox.exec_()
        if ret[1] == "True":
            msg = "Reached the maximum number of points\n"
            msg += "If you need to use more points\n"
            msg += "contact the author:\n"
            msg += qLidarDefinitions.CONST_AUTHOR_MAIL
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText(msg)
            msgBox.exec_()
        # ret = self.iPyProject.pctGetMaximumDensity(self.projectPath)
        # if ret[0] == "False":
        #     msgBox = QMessageBox(self)
        #     msgBox.setIcon(QMessageBox.Information)
        #     msgBox.setWindowTitle(self.windowTitle)
        #     msgBox.setText("Error:\n"+ret[1])
        #     msgBox.exec_()
        #     self.projectsComboBox.setCurrentIndex(0)
        #     return
        # self.maximumDensity = ret[1]
        # if self.maximumDensity > 0:
        #     dblMinimumScale = 1000.0/sqrt(self.maximumDensity)*qLidarDefinitions.CONST_POINTS_BY_MILIMETER
        #     for scale in self.scales:
        #         if scale < dblMinimumScale:
        #             self.minimumScale = scale
        #             if self.minimumScale < self.minimumValueForMinimumScale:
        #                 self.minimumScale = self.minimumValueForMinimumScale
        #             break
        # else:
        #     self.minimumScale = self.scales[3]
        ret = self.iPyProject.pctGetMaximumDensity(self.projectPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            # self.projectsComboBox.setCurrentIndex(0)
            return
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowTitle(self.windowTitle)
        strText = ''
        self.maximumDensity = ret[1]
        if self.maximumDensity > 0:
            self.minimumScale = self.scales[0]
            dblMinimumScale = 1000.0/sqrt(self.maximumDensity)*qLidarDefinitions.CONST_POINTS_BY_MILIMETER
            for scale in self.scales:
                if scale < dblMinimumScale:
                    self.minimumScale = scale
                else:
                    break
            if self.minimumScale < self.minimumValueForMinimumScale:
                self.minimumScale = self.minimumValueForMinimumScale
            strText = "Maximum density: " + str(self.maximumDensity)
            strText += "\nMinimum scale: 1/" + str(self.minimumScale)
        else:
            # self.minimumScale = self.scales[0]
            strText = "There are no points in the project"
            strText += "\nMinimum scale: 1/" + str(self.minimumScale)
        msgBox.setText(strText)
        msgBox.exec_()
        # self.projectPath = projectPath
        self.updateMinScales()
        tilesTableName = qLidarDefinitions.CONST_SPATIALITE_LAYERS_TILES_TABLE_NAME
        self.loadTilesLayer()
        layerList = QgsProject.instance().mapLayersByName(tilesTableName)
        if not layerList:
            self.projectManagementTabWidget.setTabEnabled(2, False)
        else:
            tilesLayer = layerList[0]
            if tilesLayer.featureCount() > 0:
                self.projectManagementTabWidget.setTabEnabled(2, True)
                tilesLayer.triggerRepaint()
        return

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def closeProject(self):
        if not self.projectPath:
            return
        self.openProjectPushButton.setEnabled(False)
        self.closeProjectPushButton.setEnabled(False)
        self.removeProjectPushButton.setEnabled(False)
        # delete project in ram??
        root = QgsProject.instance().layerTreeRoot()
        self.removeGroup(root,self.layerTreeProjectName)
        self.projectPath = None
        self.layerTreeProjectName = None
        self.layerTreeProject = None
        self.layerTreePCTilesName = None
        self.layerTreePCTiles = None
        self.projectsComboBox.setEnabled(True)
        self.projectsComboBox.setCurrentIndex(0)
        self.iface.mapCanvas().refresh()
        self.manualEditingProcessesPage.setEnabled(False)
        return

    def createProject(self):
        projectType = self.projectTypeComboBox.currentText()
        if projectType == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select project type")
            msgBox.exec_()
            return
        strGridSize = self.gridSizeComboBox.currentText()
        if strGridSize == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select grid size")
            msgBox.exec_()
            return
        gridSize = Decimal(strGridSize)
        crs = self.projectQgsProjectionSelectionWidget.crs()
        isValidCrs = crs.isValid()
        crsAuthId = crs.authid()
        if not "EPSG:" in crsAuthId:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not EPSG")
            msgBox.exec_()
            return
        crsEpsgCode = int(crsAuthId.replace('EPSG:',''))
        crsOsr = osr.SpatialReference()  # define test1
        if crsOsr.ImportFromEPSG(crsEpsgCode) != 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error importing OSR CRS from EPSG code" + str(crsEpsgCode))
            msgBox.exec_()
            return
        if not crsOsr.IsProjected():
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not a projected CRS")
            msgBox.exec_()
            return
        altitudeIsMsl = True
        verticalCrsEpsgCode = -1
        if self.projVersionMajor < 8:
            if self.projectAltitudeEllipsoidRadioButton.isChecked():
                altitudeIsMsl = False
        else:
            verticalCrsStr = self.verticalCRSsComboBox.currentText()
            if not verticalCrsStr == qLidarDefinitions.CONST_ELLIPSOID_HEIGHT:
                verticalCrsEpsgCode = int(verticalCrsStr.replace('EPSG:',''))
        projectPath = self.projectPathLineEdit.text()
        if not projectPath:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select project path")
            msgBox.exec_()
            return
        if projectPath in self.projects:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Exists project with selected path,\nremove it before")
            msgBox.exec_()
            return
        if len(self.roisShapefiles) == 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select one ROI at least")
            msgBox.exec_()
            return
        strRoisShapefiles = ''
        cont = 0
        for roiShapefile in self.roisShapefiles:
            if cont > 0:
                strRoisShapefiles = strRoisShapefiles + self.parametersFromPythonStringSeparator
            strRoisShapefiles = strRoisShapefiles + roiShapefile
            cont = cont + 1
        if self.projVersionMajor < 8:
            ret = self.iPyProject.pctCreateProject(projectPath,
                                                   projectType,
                                                   strGridSize,  #gridSize,
                                                   crsEpsgCode,
                                                   altitudeIsMsl,
                                                   strRoisShapefiles)
        else:
            ret = self.iPyProject.pctCreateProject(projectPath,
                                                   projectType,
                                                   strGridSize,  #gridSize,
                                                   crsEpsgCode,
                                                   verticalCrsEpsgCode,
                                                   strRoisShapefiles)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            return
        self.projects.append(projectPath)
        self.projectsComboBox.addItem(projectPath)
        strProjects = ""
        cont = 0
        for project in self.projects:
            if cont > 0:
                strProjects = strProjects + qLidarDefinitions.CONST_PROJECTS_STRING_SEPARATOR
            strProjects += project
            cont = cont + 1
        self.settings.setValue("projects", strProjects)
        self.settings.sync()
        pos = self.projectsComboBox.findText(projectPath)
        if pos >= 0:
            self.projectsComboBox.setCurrentIndex(pos)
        # connectionName = QFileInfo(dbFileName).fileName()
        # con = [connectionName, dbFileName]
        # QSettings().setValue("SpatiaLite/connections/%s/sqlitepath" % (con[0]), con[1])
        # self.iface.reloadConnections()
        # self.getSpatialiteConnections()
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowTitle(self.windowTitle)
        msgBox.setText("Process completed successfully")
        msgBox.exec_()
        return

    def initialize(self):
        self.projectPath = None
        self.layerTreeName = None
        self.layerTree = None
        # self.path_plugin = os.path.dirname(os.path.realpath(__file__))
        # # pluginPath = 'python/plugins/point_cloud_tools'
        # # pluginPath = os.path.join(QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path(), pluginPath)
        # self.path_libCpp = os.path.join(self.pluginPath, 'libCpp')
        # existsPluginPath = QDir(self.path_libCpp).exists()
        # sys.path.append(self.path_plugin)
        # sys.path.append(self.path_libCpp)
        # os.environ["PATH"] += os.pathsep + self.path_libCpp
        # self.path_plugin = pluginPath
        # self.path_libCpp = libCppPath
        self.windowTitle = qLidarDefinitions.CONST_PROGRAM_NAME
        path_file_qsettings = self.path_plugin + '/' + qLidarDefinitions.CONST_SETTINGS_FILE_NAME
        self.settings = QSettings(path_file_qsettings,QSettings.IniFormat)

        qs = QSettings()
        self.about_qdialog = None
        self.aboutPushButton.clicked.connect(self.showAboutDlg)

        # template path que cuelga del directorio de este fichero
        pluginsPath = QFileInfo(QgsApplication.qgisUserDatabaseFilePath()).path()
        thisFilePath = os.path.dirname(os.path.realpath(__file__))
        thisFilePath = os.path.join(pluginsPath, thisFilePath)
        # templatePath = os.path.join(thisFilePath, PCTDefinitions.CONST_TEMPLATE_PATH)
        self.templatePath = thisFilePath + qLidarDefinitions.CONST_TEMPLATE_PATH
        svg_paths = qs.value('svg/searchPathsForSVG')
        # if self.templatePath not in svg_paths:
            # qs.setValue('svg/searchPathsForSVG', svg_paths + [self.templatePath])
        qs.setValue('svg/searchPathsForSVG', self.templatePath)
        # if not svg_paths:
            # qs.setValue('svg/searchPathsForSVG', self.templatePath)
        # else:
            # qs.setValue('svg/searchPathsForSVG', svg_paths + [self.templatePath])

        self.qmlPointCloudFileName = self.templatePath + qLidarDefinitions.CONST_SYMBOLOGY_POINT_CLOUD_TEMPLATE
        self.qmlTilesFileName = self.templatePath + qLidarDefinitions.CONST_SYMBOLOGY_TILES_TEMPLATE
        self.qmlRoisFileName = self.templatePath + qLidarDefinitions.CONST_SYMBOLOGY_ROIS_TEMPLATE
        self.path = self.settings.value("last_path")
        if not self.path:
            self.path = QDir.currentPath()
            self.settings.setValue("last_path",self.path)
            self.settings.sync()

        self.projectManagerTemporalPath = self.settings.value("project_management_temporal_path")
        auxDir = QDir(self.path)
        if not self.projectManagerTemporalPath or not auxDir.exists(self.projectManagerTemporalPath):
            # self.projectManagerTemporalPath = self.path_libCpp + qLidarDefinitions.CONST_PROJECT_MANAGEMENT_TEMPORAL_PATH
            self.projectManagerTemporalPath = os.path.normpath(self.path_libCpp + qLidarDefinitions.CONST_PROJECT_MANAGEMENT_TEMPORAL_PATH)
            self.settings.setValue("project_management_temporal_path", self.projectManagerTemporalPath)
            self.settings.sync()
        self.pmTemporalPathLineEdit.setText(self.projectManagerTemporalPath)

        self.projectManagerOutputPath = self.settings.value("project_management_output_path")
        auxDir = QDir(self.path)
        if not self.projectManagerOutputPath or not auxDir.exists(self.projectManagerOutputPath):
            # self.projectManagerOutputPath = self.path_libCpp + qLidarDefinitions.CONST_PROJECT_MANAGEMENT_OUTPUT_PATH
            self.projectManagerOutputPath = os.path.normpath(self.path_libCpp + qLidarDefinitions.CONST_PROJECT_MANAGEMENT_OUTPUT_PATH)
            self.settings.setValue("project_management_output_path", self.projectManagerOutputPath)
            self.settings.sync()
        self.pmOutputPathLineEdit.setText(self.projectManagerOutputPath)

        self.lastoolsPath = self.settings.value("lastools_path")
        if self.lastoolsPath:
            if not auxDir.exists(self.lastoolsPath):
                self.lastoolsPath = None
            if self.lastoolsPath:
                self.ppToolsLastoolsPathLineEdit.setText(self.lastoolsPath)

        strProjects = self.settings.value("projects")
        self.projects = []
        if strProjects:
            self.projects = strProjects.split(qLidarDefinitions.CONST_PROJECTS_STRING_SEPARATOR)

        self.roisShapefiles = []
        self.roisFileTypes = []
        self.processList = []
        self.roisFileTypes.append(qLidarDefinitions.CONST_DOCUMENTS_TYPE_SHAPEFILE)
        self.roisFilesActiveFileExtensions = self.roisFileTypes
        self.pointCloudFiles = []
        self.postprocessingIPCFs = []
        self.pointCloudFilesFileTypes = []
        self.maximumDensity = 0.0
        self.minimumScale = 500
        self.minimumValueForMinimumScale = 10
        self.scales = [10,50,100,200,500,1000,2000]
        self.pointCloudFilesFileTypes.append(qLidarDefinitions.CONST_DOCUMENTS_TYPE_LASFILE)
        self.pointCloudFilesFileTypes.append(qLidarDefinitions.CONST_DOCUMENTS_TYPE_LAZFILE)
        self.pointCloudFilesActiveFileExtensions = self.pointCloudFilesFileTypes

        # spatialiteConnections = qs.value("SpatiaLite/connections")
        # self.iPyProject=IPyPCTProject()
        self.parametersFromPythonStringSeparator = self.iPyProject.getParametersFromPythonStringSeparator()
        # kk_str = self.iPyProject.output()
        # kk_list =  self.iPyProject.getVd()
        # kk_dict =  self.iPyProject.getMapSS()
        # self.iPyProject.setPythonModulePath(libCppPath)
        # ret = self.iPyProject.initialize()
        if self.isqLidarPlugin:
            ret = self.iPyProject.setPointCloudFileManager()
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n"+ret[1])
                msgBox.exec_()
                return

        self.crsEpsgCode = -1
        self.verticalCrsEpsgCode = -1
        if self.projVersionMajor >=8:
            self.projectQgsProjectionSelectionWidget.crsChanged.connect(self.setCrs)
            self.projectQgsProjectionSelectionWidget.cleared.connect(self.setCrs)
            self.verticalCRSsComboBox.addItem(qLidarDefinitions.CONST_ELLIPSOID_HEIGHT)
        self.projectQgsProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))

        if self.projVersionMajor >=8:
            self.addPCFsQgsProjectionSelectionWidget.crsChanged.connect(self.setCrsAddPCFs)
            self.addPCFsQgsProjectionSelectionWidget.cleared.connect(self.setCrsAddPCFs)
            self.addPCFsVerticalCRSsComboBox.addItem(qLidarDefinitions.CONST_ELLIPSOID_HEIGHT)
        self.addPCFsQgsProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))

        if self.projVersionMajor >=8:
            self.ppToolsIPCFsQgsProjectionSelectionWidget.crsChanged.connect(self.setCrsPpToolsIPCFs)
            self.ppToolsIPCFsQgsProjectionSelectionWidget.cleared.connect(self.setCrsPpToolsIPCFs)
            self.ppToolsIPCFsVerticalCRSsComboBox.addItem(qLidarDefinitions.CONST_ELLIPSOID_HEIGHT)
        self.ppToolsIPCFsQgsProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))

        if self.lastoolsPath:
            ret = self.iPyProject.pctSetLastoolsPath(self.lastoolsPath)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n" + ret[1])
                msgBox.exec_()
                self.ppToolsLastoolsPathLineEdit.setText("")
                self.lastoolsPath = None
                return
        ret = self.iPyProject.pctSetProjectManagerTemporalPath(self.projectManagerTemporalPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n" + ret[1])
            msgBox.exec_()
            self.pmTemporalPathLineEdit.setText("")
            self.projectManagerTemporalPath = None
            return
        ret = self.iPyProject.pctSetProjectManagerOutputPath(self.projectManagerOutputPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n" + ret[1])
            msgBox.exec_()
            self.pmOutputPathLineEdit.setText("")
            self.projectManagerOutputPath = None
            return

        self.layerTreeProject = None
        self.layerTreeProjectName = None
        self.layerTreePCTiles = None
        self.layerTreePCTilesName = None
        self.loadedTiles = []

        # set projectManagement active
        self.toolBox.setCurrentIndex(0)

        ###################################################
        # Preprocessing tools
        ###################################################

        self.lastoolsCommands = self.iPyProject.pctGetLastoolsCommands()
        self.ppToolsLastoolsCommandComboBox.addItem(qLidarDefinitions.CONST_NO_COMBO_SELECT)
        for lastoolsCommand in self.lastoolsCommands:
            self.ppToolsLastoolsCommandComboBox.addItem(lastoolsCommand)
        self.ppToolsLastoolsCommandComboBox.currentIndexChanged.connect(self.selectLastoolsCommand)
        self.selectLastoolsCommand()
        self.ppToolsLastoolsCommandParametersPushButton.setEnabled(False)

        # Parameters
        self.ppToolsLastoolsCommandParametersPushButton.clicked.connect(self.selectLastoolsCommandParameters)

        self.addProcessToListPushButton.clicked.connect(self.addProcessToList)
        self.processListEditionPushButton.clicked.connect(self.processListEdition)
        self.runProcessListPushButton.clicked.connect(self.runProcessList)

        self.ppToolsSelectIPCFsPushButton.clicked.connect(self.selectPostprocessingIPCFs)
        self.ppToolsLastoolsPathPushButton.clicked.connect(self.selectLastoolsPath)
        self.ppToolsOPCFsOutputFilePushButton.clicked.connect(self.selectPpToolsOutputFile)
        self.ppToolsOPCFsOutputPathPushButton.clicked.connect(self.selectPpToolsOutputPath)
        self.ppToolsOPCFsSuffixPushButton.clicked.connect(self.selectPpToolsOutpufFilesSuffix)
        self.ppToolsOPCFsPrefixPushButton.clicked.connect(self.selectPpToolsOutpufFilesPrefix)

        self.internalCommands = self.iPyProject.pctGetInternalCommands()
        self.ppToolsInternalCommandComboBox.addItem(qLidarDefinitions.CONST_NO_COMBO_SELECT)
        for internalCommand in self.internalCommands:
            self.ppToolsInternalCommandComboBox.addItem(internalCommand)
        self.ppToolsInternalCommandComboBox.currentIndexChanged.connect(self.selectInternalCommand)
        self.selectInternalCommand()
        self.ppToolsInternalCommandParametersPushButton.setEnabled(False)
        self.ppToolsInternalCommandParametersPushButton.clicked.connect(self.selectInternalCommandParameters)

        self.ppToolsTabWidget.currentChanged.connect(self.ppToolsTabWidgetChanged)
        self.ppToolsTabWidget.setCurrentIndex(0)


        ###################################################
        # Project Management Page
        ###################################################
        # Projects spatialite databases
        # self.getSpatialiteConnections()
        self.projectsComboBox.clear()
        self.projectsComboBox.addItem(qLidarDefinitions.CONST_NO_COMBO_SELECT)
        for project in self.projects:
            self.projectsComboBox.addItem(project)
        if self.isqLidarPlugin:
            self.projectsComboBox.currentIndexChanged.connect(self.selectProject)

        # Project
        self.addProjectPushButton.clicked.connect(self.addProject)
        self.openProjectPushButton.clicked.connect(self.openProject)
        self.closeProjectPushButton.clicked.connect(self.closeProject)
        self.removeProjectPushButton.clicked.connect(self.removeProject)

        # Project types
        self.projectTypes = self.iPyProject.pctGetProjectTypes()
        if len(self.projectTypes) > 1:
            self.projectTypeComboBox.addItem(qLidarDefinitions.CONST_NO_COMBO_SELECT)
        for projectType in self.projectTypes:
            self.projectTypeComboBox.addItem(projectType)
        self.projectTypeComboBox.currentIndexChanged.connect(self.selectProjectType)
        if len(self.projectTypes) == 1:
            self.projectTypeComboBox.setEnabled(False)

        # Grid sizes
        gridSizes = self.iPyProject.pctGetGridSizes()
        self.gridSizeComboBox.addItem(qLidarDefinitions.CONST_NO_COMBO_SELECT)
        for gridSize in gridSizes:
            strGridSize = str(round(gridSize, qLidarDefinitions.CONST_GRID_SIZE_ACCURACY))
            self.gridSizeComboBox.addItem(strGridSize)

        # Parameters
        self.projectParametersPushButton.clicked.connect(self.selectProjectParameters)

        # new project path
        self.projectPathPushButton.clicked.connect(self.selectNewProjectPath)

        self.projectManagementTabWidget.setTabEnabled(0,True)
        self.projectManagementTabWidget.setTabEnabled(1,False)
        self.projectManagementTabWidget.setCurrentIndex(0)
        self.openProjectPushButton.setEnabled(False)
        self.closeProjectPushButton.setEnabled(False)

        # ROIs
        self.roisPushButton.clicked.connect(self.selectRois)
        self.numberOfRoisLineEdit.setText("0")

        # PCFs
        self.selectPCFsPushButton.clicked.connect(self.selectPCFs)
        self.numberOfPCFsLineEdit.setText("0")
        self.addPCFsProcessPushButton.clicked.connect(self.addPointCloudFiles)

        # create
        self.createProjectPushButton.clicked.connect(self.createProject)

        # export
        self.exportPPCFsOutputPathPushButton.clicked.connect(self.exportPPCFsOutputPath)
        self.exportPPCFsSuffixPushButton.clicked.connect(self.exportPPCFsSuffix)
        self.exportPPCFsProcessPushButton.clicked.connect(self.exportPPCFsProcess)

        # reclassification confusion matrix report
        self.reclassificationConfusionMatrixReportSelectClassesPushButton.clicked.connect(self.selectReclassificationConfusionMatrixSelectClasses)
        self.reclassificationConfusionMatrixReportOutputFilePushButton.clicked.connect(self.selectReclassificationConfusionMatrixReportFile)
        self.reclassificationConfussionMatrixReportSelectedClassesRadioButton.clicked.connect(self.selectReclassificationConfusionMatrixSelectedClasses)
        self.reclassificationConfusionMatrixReportAllClassesRadioButton.clicked.connect(self.selectReclassificationConfusionMatrixReportAllClasses)
        # strReclassificationConfusionMatrixReportSelectedClasses=definitions.CONST_RCM_REPORT_DEFAULT_SELECTED_CLASSES
        strReclassificationConfusionMatrixReportSelectedClasses="2;3;4;5;6;7"
        self.reclassificationConfusionMatrixReportSelectClassesLineEdit.setText(strReclassificationConfusionMatrixReportSelectedClasses)
        self.reclassificationConfusionMatrixReportSelectClassesLineEdit.setEnabled(True)
        self.reclassificationConfussionMatrixReportSelectedClassesRadioButton.setChecked(True)
        self.reclassificationConfusionMatrixReportSelectClassesPushButton.setEnabled(True)
        self.reclassificationConfusionMatrixReportValidSelectClasses = [0,1,2,3,4,5,6,7,8,9,12]
        self.reclassificationConfusionMatrixReportProcessPushButton.clicked.connect(self.selectReclassificationConfusionMatrixReportProcess)

        # temporal path
        self.pmTemporalPathPushButton.clicked.connect(self.selectProjectManagerTemporalPath)
        self.pmOutputPathPushButton.clicked.connect(self.selectProjectManagerOutputPath)

        ###################################################
        # Manual Editing Processes Page
        ###################################################
        self.manualEditingProcessesPage.setEnabled(False)
        self.loadTilesMapCanvasPushButton.clicked.connect(self.selectLoadTilesForMapCanvas)
        self.unloadAllTilesPushButton.clicked.connect(self.unloadAllTiles)
        self.minScaleComboBox.currentIndexChanged.connect(self.selectMinScale)
        self.toolButton_SelectByRectangle.clicked.connect(self.selectPointsFromTilesByRectangle)
        self.toolButton_SelectByPolygon.clicked.connect(self.selectPointsFromTilesByPolygon)
        self.toolButton_SelectByFreehand.clicked.connect(self.selectPointsFromTilesByFreehand)
        self.toolButton_SelectByRectangle.setEnabled(False)
        self.toolButton_SelectByPolygon.setEnabled(False)
        self.toolButton_SelectByFreehand.setEnabled(False)
        self.toolButton_SelectByRectangle_3D.clicked.connect(self.selectPointsFromTilesByRectangle3D)
        self.toolButton_SelectByPolygon_3D.clicked.connect(self.selectPointsFromTilesByPolygon3D)
        self.toolButton_SelectByFreehand_3D.clicked.connect(self.selectPointsFromTilesByFreehand3D)
        self.fullTiles3dCheckBox.setChecked(True)
        self.updateClassesWithoutEditingPushButton.clicked.connect(self.updateClassesWithoutEditing)
        self.view3dMapCanvasPushButton.clicked.connect(self.view3dMapCanvas)
        self.lockedClasses={0:False,1:False,2:False,3:False,4:False,5:False,6:False,7:False,8:False,9:False,10:False,11:False,12:False,13:False}
        self.lavelSimbolByClassNumber={0:"Created",1:"Unclassified",2:"Ground",3:"Low Vegetation",4:"Medium Vegetation",
                                5:"High Vegetation",6:"Building",7:"Low Point (noise)",8:"Model Key-point (mass point)",
                                       9:"Water",12:"Overlap Points"}
        self.visibleCheckBoxByClassNumber={0: self.visibleClass0CheckBox,
                                           1: self.visibleClass1CheckBox,
                                           2: self.visibleClass2CheckBox,
                                           3: self.visibleClass3CheckBox,
                                           4: self.visibleClass4CheckBox,
                                           5: self.visibleClass5CheckBox,
                                           6: self.visibleClass6CheckBox,
                                           7: self.visibleClass7CheckBox,
                                           # 8: self.visibleClass8CheckBox,
                                           9: self.visibleClass9CheckBox,
                                           12: self.visibleClass12CheckBox}
        self.toClass0PushButton.clicked.connect(self.toClass0)
        self.toClass1PushButton.clicked.connect(self.toClass1)
        self.toClass12PushButton.clicked.connect(self.toClass12)
        self.toClass2PushButton.clicked.connect(self.toClass2)
        self.toClass3PushButton.clicked.connect(self.toClass3)
        self.toClass4PushButton.clicked.connect(self.toClass4)
        self.toClass5PushButton.clicked.connect(self.toClass5)
        self.toClass6PushButton.clicked.connect(self.toClass6)
        self.toClass7PushButton.clicked.connect(self.toClass7)
        self.toClass9PushButton.clicked.connect(self.toClass9)
        self.getAltitudeStatisticsForSelectedPointsPushButton.clicked.connect(self.selectGetAltitudeStatisticsForSelectedPoints)
        self.getDifferencesAltitudeForSelectedPointsPushButton.clicked.connect(self.selectGetDifferencesAltitudeForSelectedPoints)
        self.removeRadioButton.clicked.connect(self.enableAllClasses)
        self.recoverRadioButton.clicked.connect(self.enableAllClasses)
        self.changeClassRadioButton.clicked.connect(self.unenableAllClasses)
        self.selectOnlyRadioButton.clicked.connect(self.unenableAllClasses)
        self.unselectRadioButton.clicked.connect(self.unenableAllClasses)
        self.toOriginalClassRadioButton.clicked.connect(self.toOriginalClass)
        self.allClassesPushButton.clicked.connect(self.selectAllClasses)
        self.allClassesPushButton.setEnabled(False) # porque esta activo changeClassRadioButton
        self.getDifferencesAltitudeForSelectedPointsPushButton.setEnabled(False)
        self.visibleClass0CheckBox.setChecked(True)
        self.visibleClass1CheckBox.setChecked(True)
        self.visibleClass2CheckBox.setChecked(True)
        self.visibleClass3CheckBox.setChecked(True)
        self.visibleClass4CheckBox.setChecked(True)
        self.visibleClass5CheckBox.setChecked(True)
        self.visibleClass6CheckBox.setChecked(True)
        self.visibleClass7CheckBox.setChecked(True)
        self.visibleClass9CheckBox.setChecked(True)
        self.visibleClass12CheckBox.setChecked(True)
        self.visibleClass0CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass1CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass2CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass3CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass4CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass5CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass6CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass7CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass9CheckBox.clicked.connect(self.actionSetVisiblePoints)
        self.visibleClass12CheckBox.clicked.connect(self.actionSetVisiblePoints)

        self.multiThreadingCheckBox.stateChanged.connect(self.selectMultiThreading)
        self.multiThreadingCheckBox.setChecked(False)

        if not self.isqLidarPlugin:
            self.projectsComboBox.setEnabled(False)
        self.selectProject()

        # self.processingToolsPage.setEnabled(False)
        return

    def enableAllClasses(self):
        self.allClassesPushButton.setEnabled(True)
        return

    def exportPPCFsOutputPath(self):
        strDir = QFileDialog.getExistingDirectory(self,"Select directory",self.path,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if strDir:
            self.path = strDir
            self.settings.setValue("last_path", self.path)
            self.settings.sync()
            self.exportPPCFsOutputPathLineEdit.setText(strDir)
        return

    def exportPPCFsSuffix(self):
        oldText = self.exportPPCFsSuffixLineEdit.text()
        label = "Input suffix for exported point cloud files:"
        title = qLidarDefinitions.CONST_PROGRAM_TITLE
        [text, ok] = QInputDialog.getText(self, title, label, QLineEdit.Normal, oldText)
        if ok and text:
            text = text.strip()
            if not text == oldText:
                self.exportPPCFsSuffixLineEdit.setText(text)
        return

    def exportPPCFsProcess(self):
        outputPath = self.exportPPCFsOutputPathLineEdit.text()
        suffix = self.exportPPCFsSuffixLineEdit.text()
        if not outputPath and not suffix:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("You must select an output folder or a suffix for export processeed point cloud files")
            msgBox.exec_()
            return
        initialDateTime = QDateTime.currentDateTime()
        ret = self.iPyProject.pctExportProcessedPointCloudFiles(self.projectPath,
                                                                suffix,
                                                                outputPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            return
        else:
            finalDateTime = QDateTime.currentDateTime()
            initialSeconds = initialDateTime.toTime_t()
            finalSeconds = finalDateTime.toTime_t()
            totalDurationSeconds = finalSeconds - initialSeconds
            durationDays = floor(totalDurationSeconds / 60.0 / 60.0 / 24.0)
            durationHours = floor((totalDurationSeconds - durationDays * 60.0 * 60.0 * 24.0) / 60.0 / 60.0)
            durationMinutes = floor((totalDurationSeconds - durationDays * 60.0 * 60.0 * 24.0 - durationHours * 60.0 * 60.0) / 60.0)
            durationSeconds = totalDurationSeconds - durationDays * 60.0 * 60.0 * 24.0 - durationHours * 60.0 * 60.0 - durationMinutes * 60.0
            msgTtime = "- Process time:\n"
            msgTtime += "  - Start time of the process ......................: "
            msgTtime += initialDateTime.toString("yyyy/MM/dd - hh/mm/ss.zzz")
            msgTtime += "\n"
            msgTtime += "  - End time of the process ........................: "
            msgTtime += finalDateTime.toString("yyyy/MM/dd - hh/mm/ss.zzz")
            msgTtime += "\n"
            msgTtime += "  - Number of total seconds ........................: "
            msgTtime += f"{totalDurationSeconds:.3f}" # QString.number(totalDurationSeconds, 'f', 3)
            msgTtime += "\n"
            msgTtime += "    - Number of days ...............................: "
            msgTtime += str(durationDays) # QString.number(durationDays)
            msgTtime += "\n"
            msgTtime += "    - Number of hours ..............................: "
            msgTtime += str(durationHours) # QString.number(durationHours)
            msgTtime += "\n"
            msgTtime += "    - Number of minutes ............................: "
            msgTtime += str(durationMinutes) # QString.number(durationMinutes)
            msgTtime += "\n"
            msgTtime += "    - Number of seconds ............................: "
            msgTtime += f"{durationSeconds:.3f}" # QString.number(durationSeconds, 'f', 3)
            msgTtime += "\n"
            msg = "Process completed successfully"
            msg += "\n"
            msg += msgTtime
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText(msg)
            msgBox.exec_()
        return

    def getChangedPoints(self):
        changedPoints = []
        changedTileNames = []
        for loadTile in self.loadedTiles:
            layers = QgsProject.instance().mapLayersByName(loadTile)
            if len(layers) == 1:
                layer = layers[0]
                if layer.type() == QgsMapLayer.VectorLayer:
                    features = layer.getFeatures()
                    for feature in features:
                        point = []
                        pointClass = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS]
                        pointNewClass = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW]
                        if pointNewClass != pointClass:
                            point.append(loadTile)
                            point.append(feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_FILE_ID])
                            point.append(feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_POSITION])
                            point.append(feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW])
                            point.append(feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS])
                            changedPoints.append(point)
                            if not loadTile in changedTileNames:
                                changedTileNames.append(loadTile)
        return [changedPoints,changedTileNames]

    # def getProjectPath(self):
    #     projectPath = self.projectsComboBox.currentText()
    #     if projectPath == qLidarDefinitions.CONST_NO_COMBO_SELECT:
    #         projectPath = ''
    #         return projectPath

    def getSelectedPoints(self):
        selectedPoints = []
        selectedTileNames = []
        for loadTile in self.loadedTiles:
            layers = QgsProject.instance().mapLayersByName(loadTile)
            if len(layers) == 1:
                layer = layers[0]
                if layer.type() == QgsMapLayer.VectorLayer:
                    features = layer.selectedFeatures()
                    for feature in features:
                        point = []
                        point.append(loadTile)
                        point.append(feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_FILE_ID])
                        point.append(feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_POSITION])
                        # point.append(feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW])
                        # point.append(feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS])
                        selectedPoints.append(point)
                        if not loadTile in selectedTileNames:
                            selectedTileNames.append(loadTile)
        return [selectedPoints,selectedTileNames]

    def loadROIsLayer(self):
        roisTableName = qLidarDefinitions.CONST_SPATIALITE_LAYERS_ROIS_TABLE_NAME
        layerList = QgsProject.instance().mapLayersByName(roisTableName)
        if layerList:
            return
        ret = self.iPyProject.pctGetROIsWktGeometry(self.projectPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            return
        numberOfRois = ret[1]
        if numberOfRois == 0:
            return
        vlayer = QgsVectorLayer("Polygon?crs=EPSG:" + str(self.crsEpsgCode), roisTableName, "memory")
        vprovider = vlayer.dataProvider()  # need to create a data provider
        vprovider.addAttributes([QgsField('id', QVariant.String)])
        vlayer.updateFields()
        featureList = []
        fields = vlayer.fields()
        for i in range(numberOfRois):
            pos = 2 + i*2
            roiId = ret[pos]
            roiWkt = ret[pos+1]
            ## now add the computed points to the layer
            feature = QgsFeature()
            feature.setFields(fields)
            feature['id'] = roiId
            feature.setGeometry(QgsGeometry.fromWkt(roiWkt))
            featureList.append(feature)
        vlayer.dataProvider().addFeatures(featureList)
        vlayer.commitChanges()
        if vlayer.isValid():
            QgsProject.instance().addMapLayer(vlayer, False)
            root = QgsProject.instance().layerTreeRoot()
            self.layerTreeProject = root.findGroup(self.layerTreeProjectName)
            if not self.layerTreeProject:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Layers group: " + self.layerTreeProjectName
                               + " not found\nClose and reload the project")
                msgBox.exec_()
                return
            self.layerTreeProject.insertChildNode(1, QgsLayerTreeLayer(vlayer))
            vlayer.loadNamedStyle(self.qmlRoisFileName)
            vlayer.triggerRepaint()
            self.iface.setActiveLayer(vlayer)
            self.iface.zoomToActiveLayer()
        else:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Impossible to Load layer: " + roisTableName
                           + " into QGIS")
            msgBox.exec_()
            return
        return

    def loadTilesLayer(self):
        tilesTableName = qLidarDefinitions.CONST_SPATIALITE_LAYERS_TILES_TABLE_NAME
        layerList = QgsProject.instance().mapLayersByName(tilesTableName)
        if layerList:
            vl = layerList[0]
            QgsProject.instance().removeMapLayers([vl.id()])
        ret = self.iPyProject.pctGetTilesWktGeometry(self.projectPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            return
        numberOfTiles = ret[1]
        if numberOfTiles == 0:
            return
        vlayer = QgsVectorLayer("Polygon?crs=EPSG:" + str(self.crsEpsgCode), tilesTableName, "memory")
        vprovider = vlayer.dataProvider()  # need to create a data provider
        vprovider.addAttributes([QgsField('id', QVariant.String)])
        vlayer.updateFields()
        featureList = []
        fields = vlayer.fields()
        for i in range(numberOfTiles):
            pos = 2 + i*2
            tileId = ret[pos]
            tileWkt = ret[pos+1]
            ## now add the computed points to the layer
            feature = QgsFeature()
            feature.setFields(fields)
            feature['id'] = tileId
            feature.setGeometry(QgsGeometry.fromWkt(tileWkt))
            featureList.append(feature)
        vlayer.dataProvider().addFeatures(featureList)
        vlayer.commitChanges()
        if vlayer.isValid():
            QgsProject.instance().addMapLayer(vlayer, False)
            root = QgsProject.instance().layerTreeRoot()
            self.layerTreeProject = root.findGroup(self.layerTreeProjectName)
            if not self.layerTreeProject:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Layers group: " + self.layerTreeProjectName
                               + " not found\nClose and reload the project")
                msgBox.exec_()
                return
            self.layerTreeProject.insertChildNode(1, QgsLayerTreeLayer(vlayer))
            vlayer.loadNamedStyle(self.qmlTilesFileName)
            vlayer.triggerRepaint()
            self.iface.setActiveLayer(vlayer)
            self.iface.zoomToActiveLayer()
        else:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Impossible to Load layer: " + tilesTableName
                           + " into QGIS")
            msgBox.exec_()
            return
        return

    def openProject(self):
        self.manualEditingProcessesPage.setEnabled(False)
        self.closeProjectPushButton.setEnabled(False)
        self.removeProjectPushButton.setEnabled(False)
        self.projectPath = None
        self.layerTreeName = None
        self.layerTree = None
        projectPath = self.projectsComboBox.currentText()
        if projectPath == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select project before")
            msgBox.exec_()
            return
        ret = self.iPyProject.pctOpenProject(projectPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            self.projectsComboBox.setCurrentIndex(0)
            return
        if ret[1] == "True":
            msg = "Reached the maximum number of points\n"
            msg += "If you need to use more points\n"
            msg += "contact the author:\n"
            msg += qLidarDefinitions.CONST_AUTHOR_MAIL
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText(msg)
            msgBox.exec_()
        if self.projVersionMajor < 8:
            ret = self.iPyProject.pctGetProjectCrsEpsgCode(projectPath)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n" + ret[1])
                msgBox.exec_()
                self.projectsComboBox.setCurrentIndex(0)
                return
            self.crsEpsgCode = ret[1]
            strCrsEpsgCode = qLidarDefinitions.CONST_EPSG_PREFIX + str(self.crsEpsgCode)
            self.addPCFsQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(strCrsEpsgCode))
            # self.addPCFsQgsProjectionSelectionWidget.setCrs(
            #     QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            self.addPCFsQgsProjectionSelectionWidget.setEnabled(False)
        else:
            ret = self.iPyProject.pctGetProjectCrsEpsgCodes(projectPath)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n"+ret[1])
                msgBox.exec_()
                self.projectsComboBox.setCurrentIndex(0)
                return
            self.crsEpsgCode = ret[1]
            self.verticalCrsEpsgCode = ret[2]
            strCrsEpsgCode = qLidarDefinitions.CONST_EPSG_PREFIX + str(self.crsEpsgCode)
            self.addPCFsQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(strCrsEpsgCode))
            # self.addPCFsQgsProjectionSelectionWidget.setCrs(
            #     QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            self.setCrsAddPCFs()
            self.addPCFsVerticalCRSsComboBox.setCurrentIndex(0)
            if self.verticalCrsEpsgCode != -1:
                strVerticalCrsEpsgCode = qLidarDefinitions.CONST_EPSG_PREFIX + str(self.verticalCrsEpsgCode)
                index = self.addPCFsVerticalCRSsComboBox.findText(strVerticalCrsEpsgCode, Qt.MatchFixedString)
                if index != -1:
                    self.addPCFsVerticalCRSsComboBox.setCurrentIndex(index)
            self.addPCFsQgsProjectionSelectionWidget.setEnabled(False)
            self.addPCFsVerticalCRSsComboBox.setEnabled(False)

        ret = self.iPyProject.pctGetMaximumDensity(projectPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            self.projectsComboBox.setCurrentIndex(0)
            return

        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowTitle(self.windowTitle)
        strText = ''
        self.maximumDensity = ret[1]
        if self.maximumDensity > 0:
            self.minimumScale = self.scales[0]
            dblMinimumScale = 1000.0/sqrt(self.maximumDensity)*qLidarDefinitions.CONST_POINTS_BY_MILIMETER
            for scale in self.scales:
                if scale < dblMinimumScale:
                    self.minimumScale = scale
                else:
                    break
            if self.minimumScale < self.minimumValueForMinimumScale:
                self.minimumScale = self.minimumValueForMinimumScale
            strText = "Maximum density: " + str(self.maximumDensity)
            strText += "\nMinimum scale: 1/" + str(self.minimumScale)
        else:
            # self.minimumScale = self.scales[0]
            strText = "There are no points in the project"
            strText += "\nMinimum scale: 1/" + str(self.minimumScale)
        msgBox.setText(strText)
        msgBox.exec_()
        self.projectPath = projectPath
        self.updateMinScales()
        groupName = qLidarDefinitions.CONST_LAYER_TREE_PROJECT_NAME
        self.layerTreeProjectName = groupName #+ connectionFileName
        root = QgsProject.instance().layerTreeRoot()
        # self.layerTreeProject = root.addGroup(self.layerTreeProjectName)
        self.layerTreeProject = root.insertGroup(0,self.layerTreeProjectName)
        self.loadROIsLayer()
        self.loadTilesLayer()
        self.loadTilesLayer()
        self.closeProjectPushButton.setEnabled(True)
        self.openProjectPushButton.setEnabled(False)
        self.projectsComboBox.setEnabled(False)
        self.projectManagementTabWidget.setEnabled(True)
        self.projectManagementTabWidget.setTabEnabled(0, False)
        self.projectManagementTabWidget.setTabEnabled(1, True)
        # self.setCrsAddPCFs()
        tilesTableName = qLidarDefinitions.CONST_SPATIALITE_LAYERS_TILES_TABLE_NAME
        layerList = QgsProject.instance().mapLayersByName(tilesTableName)
        if not layerList:
            self.projectManagementTabWidget.setTabEnabled(2, False)
        else:
            tilesLayer = layerList[0]
            if tilesLayer.featureCount() > 0:
                self.projectManagementTabWidget.setTabEnabled(2, True)
        self.manualEditingProcessesPage.setEnabled(True)
        # # msgBox = QMessageBox(self)
        # # msgBox.setIcon(QMessageBox.Information)
        # # msgBox.setWindowTitle(self.windowTitle)
        # # msgBox.setText("Process completed successfully")
        # # msgBox.exec_()
        ret = self.iPyProject.pctSetProjectManagerTemporalPath(self.projectManagerTemporalPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n" + ret[1])
            msgBox.exec_()
            return
        ret = self.iPyProject.pctSetProjectManagerOutputPath(self.projectManagerOutputPath)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n" + ret[1])
            msgBox.exec_()
            return
        return

    def ppToolsTabWidgetChanged(self,i):
        if i==0:
            self.addProcessToListPushButton.setVisible(True)
            self.processListEditionPushButton.setVisible(True)
            self.runProcessListPushButton.setText(qLidarDefinitions.CONST_PROCESSING_TOOLS_RUN_BUTTON_PROCESS_LIST_TEXT)
        if i==1:
            self.addProcessToListPushButton.setVisible(False)
            self.processListEditionPushButton.setVisible(False)
            self.runProcessListPushButton.setText(qLidarDefinitions.CONST_PROCESSING_TOOLS_RUN_BUTTON_PROCESS_TEXT)
        return

    def processListEdition(self):
        previousProcessList = self.processList[:] # copia desligada
        dlg = ProcessListEditonDialog(qLidarDefinitions.CONST_PROCESS_LIST_EDITION_DIALOG_TITLE,
                                      self.processList)
        dlg.show() # show the dialog
        result = dlg.exec_() # Run the dialog
        processList = dlg.getProcessList() # los hay repetidos
        self.processList = []
        for process in processList:
            self.processList.append(process)
        return

    def refreshMapCanvas(self):
        currentScale = self.iface.mapCanvas().scale()
        newScale = currentScale * 1.001
        self.iface.mapCanvas().zoomScale(newScale)

    def removeGroup(self,root,name):
        # root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(name)
        if not group is None:
            for child in group.children():
                dump = child.dump()
                id = dump.split("=")[-1].strip()
                QgsProject.instance().removeMapLayer(id)
            root.removeChildNode(group)
        return

    def debugNeighbors(self):
        # if not self.projVersionMajor>=8:
        #     return
        projectPath = self.projectsComboBox.currentText()
        if projectPath == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select project before")
            msgBox.exec_()
            return
        # projectCrs = QgsProject.instance().crs()
        # projectCrsEpsgCode = -1
        # projectCrsProj4 = ""
        # projectCrsAuthId = projectCrs.authid()
        # if "EPSG" in projectCrsAuthId:
        #     projectCrsEpsgCode = int(projectCrsAuthId.replace("EPSG:",""))
        # projectCrsProj4 = projectCrs.toProj4()
        point = []
        point.append(-1.893331248)
        point.append(39.018813384)
        pointCrsEpsgCode = 4258
        pointCrsProj4String = "+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs"
        searchRadius2d = 20.0
        numberOfNeighbors = 10
        ret = self.iPyProject.pctGetPointsNeighborsFromPoint(projectPath,
                                                             point,
                                                             pointCrsEpsgCode,
                                                             pointCrsProj4String,
                                                             searchRadius2d,
                                                             numberOfNeighbors)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            return
        else:
            text = "Number of neighbors: "+str(len(ret[1]))
            cont = 0
            for point in ret[1]:
                cont = cont + 1
                text += "\nPoint : " + str(cont)
                for key in point:
                    text += ";" + key + ": " + str(point[key])
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText(text)
            msgBox.exec_()
            return

    def selectGetAltitudeStatisticsForSelectedPoints(self):
        # self.debugNeighbors()
        self.meanAltitudeLineEdit.clear()
        self.stdAltitudeLineEdit.clear()
        self.altitudeDifferenceLineEdit.clear()
        self.getDifferencesAltitudeForSelectedPointsPushButton.setEnabled(False)
        meanAltitude = 0.
        altitudes = []
        numberOfSelectedPoints = 0
        for loadTile in self.loadedTiles:
            layers = QgsProject.instance().mapLayersByName(loadTile)
            if len(layers) == 1:
                layer = layers[0]
                if layer.type() == QgsMapLayer.VectorLayer:
                    features = layer.selectedFeatures()
                    for feature in features:
                        altitude = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_ALTITUDE]
                        if altitude < qLidarDefinitions.CONST_MINIMUM_HEIGHT:
                            continue
                        altitudes.append(altitude)
                        meanAltitude = meanAltitude + altitude
                        numberOfSelectedPoints = numberOfSelectedPoints + 1
        if numberOfSelectedPoints == 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select one point at least")
            msgBox.exec_()
            return
        meanAltitude = meanAltitude / numberOfSelectedPoints
        stdAltitude = 0.
        if numberOfSelectedPoints > 1:
            for altitude in altitudes:
                stdAltitude = stdAltitude + pow(meanAltitude-altitude,2.)
                stdAltitude = sqrt(stdAltitude/(numberOfSelectedPoints-1))/sqrt(numberOfSelectedPoints)
        self.meanAltitudeLineEdit.setText("{:.3f}".format(meanAltitude))
        self.stdAltitudeLineEdit.setText("{:.3f}".format(stdAltitude))
        self.getDifferencesAltitudeForSelectedPointsPushButton.setEnabled(True)
        return

    def selectMinScale(self):
        strScale = self.minScaleComboBox.currentText()
        values = strScale.split('/')
        scale = float(values[1])
        for loadTile in self.loadedTiles:
            layers = QgsProject.instance().mapLayersByName(loadTile)
            if len(layers) == 1:
                vlayer = layers[0]
                vlayer.setMinimumScale(scale)
                # vlayer.triggerRepaint()
        self.iface.mapCanvas().zoomScale(scale-1)
        return

    def selectMultiThreading(self):
        useMultiProcess=self.multiThreadingCheckBox.isChecked()
        ret = self.iPyProject.pctSetMultiProcess(useMultiProcess)
        if ret[0] == "False":
            self.multiThreadingCheckBox.setChecked(False)
            self.multiThreadingCheckBox.setEnabled(False)
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            # self.projectsComboBox.setCurrentIndex(0)
            return

    def selectPointsFromTilesByRectangle(self):
        self.toolButton_SelectByRectangle.setChecked(True)
        self.toolButton_SelectByPolygon.setChecked(False)
        self.toolButton_SelectByFreehand.setChecked(False)
        self.toolButton_SelectByRectangle_3D.setChecked(False)
        self.toolButton_SelectByPolygon_3D.setChecked(False)
        self.toolButton_SelectByFreehand_3D.setChecked(False)
        # self.toolRectangle = RectangleMapTool(self.iface.mapCanvas())
        self.toolRectangle = RectangleMapTool(self.iface.mapCanvas(),
                                              self.loadedTiles)
        self.iface.mapCanvas().setMapTool(self.toolRectangle)
        # self.iface.mapCanvas().unsetMapTool(self.toolRectangle)
        return

    def selectPointsFromTilesByRectangle3D(self):
        self.toolButton_SelectByRectangle.setChecked(False)
        self.toolButton_SelectByPolygon.setChecked(False)
        self.toolButton_SelectByFreehand.setChecked(False)
        self.toolButton_SelectByRectangle_3D.setChecked(True)
        self.toolButton_SelectByPolygon_3D.setChecked(False)
        self.toolButton_SelectByFreehand_3D.setChecked(False)
        # self.toolRectangle = RectangleMapTool(self.iface.mapCanvas())
        selectPoints = False
        self.toolRectangle3D = None
        self.toolPolygon3D = None
        self.toolFreehand3D = None
        self.toolRectangle3D = RectangleMapTool(self.iface.mapCanvas(),
                                              self.loadedTiles,
                                              selectPoints)
        self.iface.mapCanvas().setMapTool(self.toolRectangle3D)
        self.toolRectangle3D.endSelection.connect(self.view3DSelectedPoints)
        # self.iface.mapCanvas().unsetMapTool(self.toolRectangle3D)
        return

    def selectPointsFromTilesByFreehand(self):
        self.toolButton_SelectByRectangle.setChecked(False)
        self.toolButton_SelectByPolygon.setChecked(False)
        self.toolButton_SelectByFreehand.setChecked(True)
        self.toolButton_SelectByRectangle_3D.setChecked(False)
        self.toolButton_SelectByPolygon_3D.setChecked(False)
        self.toolButton_SelectByFreehand_3D.setChecked(False)
        self.toolFreehand= FreehandMapTool(self.iface.mapCanvas(),
                                              self.loadedTiles)
        self.iface.mapCanvas().setMapTool(self.toolFreehand)
        # self.iface.mapCanvas().unsetMapTool(self.toolFreehand)
        return

    def selectPointsFromTilesByFreehand3D(self):
        # self.toolRectangle = RectangleMapTool(self.iface.mapCanvas())
        self.toolButton_SelectByRectangle.setChecked(False)
        self.toolButton_SelectByPolygon.setChecked(False)
        self.toolButton_SelectByFreehand.setChecked(False)
        self.toolButton_SelectByRectangle_3D.setChecked(False)
        self.toolButton_SelectByPolygon_3D.setChecked(False)
        self.toolButton_SelectByFreehand_3D.setChecked(True)
        selectPoints = False
        self.toolRectangle3D = None
        self.toolPolygon3D = None
        self.toolFreehand3D = None
        self.toolFreehand3D = FreehandMapTool(self.iface.mapCanvas(),
                                              self.loadedTiles,
                                              selectPoints)
        self.iface.mapCanvas().setMapTool(self.toolFreehand3D)
        self.toolFreehand3D.endSelection.connect(self.view3DSelectedPoints)
        # self.iface.mapCanvas().unsetMapTool(self.toolFreehand3D)
        return

    def selectPointsFromTilesByPolygon(self):
        self.toolButton_SelectByRectangle.setChecked(False)
        self.toolButton_SelectByPolygon.setChecked(True)
        self.toolButton_SelectByFreehand.setChecked(False)
        self.toolButton_SelectByRectangle_3D.setChecked(False)
        self.toolButton_SelectByPolygon_3D.setChecked(False)
        self.toolButton_SelectByFreehand_3D.setChecked(False)
        self.toolPolygon= PolygonMapTool(self.iface.mapCanvas(),
                                              self.loadedTiles)
        self.iface.mapCanvas().setMapTool(self.toolPolygon)
        # self.iface.mapCanvas().unsetMapTool(self.toolPolygon)
        return

    def selectPointsFromTilesByPolygon3D(self):
        # self.toolRectangle = RectangleMapTool(self.iface.mapCanvas())
        self.toolButton_SelectByRectangle.setChecked(False)
        self.toolButton_SelectByPolygon.setChecked(False)
        self.toolButton_SelectByFreehand.setChecked(False)
        self.toolButton_SelectByRectangle_3D.setChecked(False)
        self.toolButton_SelectByPolygon_3D.setChecked(True)
        self.toolButton_SelectByFreehand_3D.setChecked(False)
        selectPoints = False
        self.toolRectangle3D = None
        self.toolPolygon3D = None
        self.toolFreehand3D = None
        self.toolPolygon3D = PolygonMapTool(self.iface.mapCanvas(),
                                              self.loadedTiles,
                                              selectPoints)
        self.iface.mapCanvas().setMapTool(self.toolPolygon3D)
        self.toolPolygon3D.endSelection.connect(self.view3DSelectedPoints)
        # self.iface.mapCanvas().unsetMapTool(self.toolPolygon3D)
        return

    def selectGetDifferencesAltitudeForSelectedPoints(self):
        self.altitudeDifferenceLineEdit.clear()
        numberOfSelectedPoints = 0
        altitude = 0.
        for loadTile in self.loadedTiles:
            layers = QgsProject.instance().mapLayersByName(loadTile)
            if len(layers) == 1:
                layer = layers[0]
                if layer.type() == QgsMapLayer.VectorLayer:
                    features = layer.selectedFeatures()
                    for feature in features:
                        altitude = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_ALTITUDE]
                        numberOfSelectedPoints = numberOfSelectedPoints + 1
        if numberOfSelectedPoints < 0 or numberOfSelectedPoints > 1:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select a single point")
            msgBox.exec_()
            return
        strMeanAltitude = self.meanAltitudeLineEdit.text()
        meanAltitude = float(strMeanAltitude)
        altitude_diff = altitude - meanAltitude
        self.altitudeDifferenceLineEdit.setText("{:.3f}".format(altitude_diff))
        return

    def selectInternalCommand(self):
        self.ppToolsOPCFsOutputFilePushButton.setEnabled(False)
        self.ppToolsOPCFsOutputFileLineEdit.setText("")
        self.ppToolsOPCFsOutputPathPushButton.setEnabled(False)
        self.ppToolsOPCFsOutputPathLineEdit.setText("")
        self.ppToolsOPCFsSuffixPushButton.setEnabled(False)
        self.ppToolsOPCFsSuffixLineEdit.setText("")
        self.ppToolsOPCFsPrefixPushButton.setEnabled(False)
        self.ppToolsOPCFsPrefixLineEdit.setText("")
        internalCommand = self.ppToolsInternalCommandComboBox.currentText()
        if internalCommand == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            self.ppToolsInternalCommandParametersPushButton.setEnabled(False)
            return
        ret = self.iPyProject.pctGetInternalCommandsOutputDataFormat(internalCommand)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            return
        if ret[1] == "True":
            self.ppToolsOPCFsOutputPathPushButton.setEnabled(True)
        if ret[2] == "True":
            self.ppToolsOPCFsOutputFilePushButton.setEnabled(True)
        if ret[3] == "True":
            self.ppToolsOPCFsSuffixPushButton.setEnabled(True)
        if ret[4] == "True":
            self.ppToolsOPCFsPrefixPushButton.setEnabled(True)
        self.ppToolsInternalCommandParametersPushButton.setEnabled(True)
        return

    def selectLastoolsCommand(self):
        self.ppToolsOPCFsOutputFilePushButton.setEnabled(False)
        self.ppToolsOPCFsOutputFileLineEdit.setText("")
        self.ppToolsOPCFsOutputPathPushButton.setEnabled(False)
        self.ppToolsOPCFsOutputPathLineEdit.setText("")
        self.ppToolsOPCFsSuffixPushButton.setEnabled(False)
        self.ppToolsOPCFsSuffixLineEdit.setText("")
        self.ppToolsOPCFsPrefixPushButton.setEnabled(False)
        self.ppToolsOPCFsPrefixLineEdit.setText("")
        lastoolsCommand = self.ppToolsLastoolsCommandComboBox.currentText()
        if lastoolsCommand == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            self.ppToolsLastoolsCommandParametersPushButton.setEnabled(False)
            return
        ret = self.iPyProject.pctGetLastoolsCommandsOutputDataFormat(lastoolsCommand)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            return
        if ret[1] == "True":
            self.ppToolsOPCFsOutputPathPushButton.setEnabled(True)
        if ret[2] == "True":
            self.ppToolsOPCFsOutputFilePushButton.setEnabled(True)
        if ret[3] == "True":
            self.ppToolsOPCFsSuffixPushButton.setEnabled(True)
        if ret[4] == "True":
            self.ppToolsOPCFsPrefixPushButton.setEnabled(True)
        self.ppToolsLastoolsCommandParametersPushButton.setEnabled(True)
        return

    def selectInternalCommandParameters(self):
        internalCommand = self.ppToolsInternalCommandComboBox.currentText()
        if internalCommand == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select internal command before")
            msgBox.exec_()
            return
        ret = self.iPyProject.pctSelectInternalCommandParameters(internalCommand)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
        return

    def selectLastoolsCommandParameters(self):
        lastoolsCommand = self.ppToolsLastoolsCommandComboBox.currentText()
        if lastoolsCommand == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select lastools command before")
            msgBox.exec_()
            return
        ret = self.iPyProject.pctSelectLastoolsCommandParameters(lastoolsCommand)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
        return

    def selectLastoolsPath(self):
        strDir = QFileDialog.getExistingDirectory(self,"Select directory",self.path,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if strDir:
            ret = self.iPyProject.pctSetLastoolsPath(strDir)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n" + ret[1])
                msgBox.exec_()
                self.ppToolsLastoolsPathLineEdit.setText("")
                self.lastoolsPath = None
                return
            self.lastoolsPath = strDir
            self.settings.setValue("lastools_path", self.lastoolsPath)
            self.settings.sync()
            self.ppToolsLastoolsPathLineEdit.setText(strDir)
        return

    def selectLoadTilesForMapCanvas(self):
        mapCanvasExtend = self.iface.mapCanvas().extent()
        maxFc = mapCanvasExtend.xMaximum()
        maxSc = mapCanvasExtend.yMaximum()
        minFc = mapCanvasExtend.xMinimum()
        minSc = mapCanvasExtend.yMinimum()
        mapCanvasWkt = 'POLYGON((' + str(minFc)+ ' '+str(maxSc) + ',' \
                        + str(maxFc) + ' ' + str(maxSc) + ',' \
                        + str(maxFc) + ' ' + str(minSc) + ',' \
                        + str(minFc) + ' ' + str(minSc) + ',' \
                        + str(minFc) + ' ' + str(maxSc) + '))'
        # mapCanvasGeometry = ogr.CreateGeometryFromWkt(mapCanvasWkt)
        # epsgCode = int(self.lidarFilesCrs.authid().replace("EPSG:",""))
        projectCrs = QgsProject.instance().crs()
        projectCrsEpsgCode = -1
        projectCrsProj4 = ""
        projectCrsAuthId = projectCrs.authid()
        if "EPSG" in projectCrsAuthId:
            projectCrsEpsgCode = int(projectCrsAuthId.replace("EPSG:",""))
        projectCrsProj4 = projectCrs.toProj4()
        ret = self.iPyProject.pctGetTilesFromWktGeometry(self.projectPath,
                                                         mapCanvasWkt,
                                                         projectCrsEpsgCode,
                                                         projectCrsProj4)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n" + ret[1])
            msgBox.exec_()
            return
        if ret[1] == 0:
            text = "There are no new tiles to load"
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText(text)
            msgBox.exec_()
            return
        numberOfNotLoadedTiles = 0
        numberOfLoadedTiles = len(self.loadedTiles)
        initialTileNames = ret[2]
        for tileX in initialTileNames:
            for tileY in initialTileNames[tileX]:
                tileName = initialTileNames[tileX][tileY]
                if not tileName in self.loadedTiles:
                    numberOfNotLoadedTiles= numberOfNotLoadedTiles + 1
        if numberOfNotLoadedTiles == 0:
            text = "There are no tiles to load"
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText(text)
            msgBox.exec_()
            return
        if numberOfNotLoadedTiles > 0:
            numberOfTiles = ret[1]
            # tilesNames =ret[2]
            numberOfTotalTiles = numberOfNotLoadedTiles + numberOfLoadedTiles
            if qLidarDefinitions.CONST_MAX_POINT_TILES > 0:
                if numberOfTotalTiles > qLidarDefinitions.CONST_MAX_POINT_TILES:
                    text = "The number of tiles to load is limited to "
                    text += str(qLidarDefinitions.CONST_MAX_POINT_TILES)
                    text += "\nto avoid performance problems"
                    msgBox = QMessageBox(self)
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setWindowTitle(self.windowTitle)
                    msgBox.setText(text)
                    msgBox.exec_()
                    # text = str(numberOfTiles) + " tiles will be loaded"
                    # text += "\n\nContinue?"
                    # reply = QMessageBox.question(self.iface.mainWindow(), qLidarDefinitions.CONST_PROGRAM_TITLE,
                    #                              text, QMessageBox.Yes, QMessageBox.No)
                    # if reply == QMessageBox.No:
                    #     return
                    return
            ret = self.iPyProject.pctGetPointsFromWktGeometry(self.projectPath,
                                                             mapCanvasWkt,
                                                             projectCrsEpsgCode,
                                                             projectCrsProj4,
                                                             self.loadedTiles)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n" + ret[1])
                msgBox.exec_()
                return
            if not self.layerTreePCTiles:
                self.layerTreePCTilesName = qLidarDefinitions.CONST_LAYER_TREE_PCTILES_NAME
                # self.layerTreePCTiles = self.layerTreeProject.addGroup(self.layerTreePCTilesName)
                root = QgsProject.instance().layerTreeRoot()
                self.layerTreeProject = root.findGroup(self.layerTreeProjectName)
                if not self.layerTreeProject:
                    msgBox = QMessageBox(self)
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setWindowTitle(self.windowTitle)
                    msgBox.setText("Layers group: " + self.layerTreeProjectName
                                   + " not found\nClose and reload the project")
                    msgBox.exec_()
                    return
                self.layerTreePCTiles = self.layerTreeProject.addGroup(self.layerTreePCTilesName)
            # si no se cargan nuevos
            if len(ret) > 1:
                tilesNames = ret[1] # QMap<int,QMap<int,QString> >
                existsFieldsByFileId = ret[2] # QMap<int,QMap<QString,bool> >

                # pointDict[POINTCLOUDFILE_PYTHON_TAG_POSITION_TILE] = posInTile;
                # pointDict[POINTCLOUDFILE_PYTHON_TAG_IX] = ix;
                # pointDict[POINTCLOUDFILE_PYTHON_TAG_IY] = iy;
                # pointDict[POINTCLOUDFILE_PYTHON_TAG_Z] = z;
                # pointDict[POINTCLOUDFILE_PYTHON_TAG_CLASS] = ptoClass;
                # pointDict[POINTCLOUDFILE_PYTHON_TAG_CLASS_NEW] = ptoNewClass;
                # pointDict[POINTCLOUDFILE_PYTHON_TAG_GPS_TIME] = gpsTime;
                # pointDict[POINTCLOUDFILE_PYTHON_TAG_VALUES_8BITS] = values8BitsDict;
                # pointDict[POINTCLOUDFILE_PYTHON_TAG_VALUES_16BITS] = values16BitsDict;
                pointsByTileByFileId = ret[3] # QMap<int,QMap<int,QMap<int,QVector<PCFile::Point> > > >

                # existsFields[POINTCLOUDFILE_PARAMETER_COLOR] = false;
                # existsFields[POINTCLOUDFILE_PARAMETER_GPS_TIME] = false;
                # existsFields[POINTCLOUDFILE_PARAMETER_INTENSITY] = false;
                # existsFields[POINTCLOUDFILE_PARAMETER_NIR] = false;
                # existsFields[POINTCLOUDFILE_PARAMETER_RETURN] = false;
                # existsFields[POINTCLOUDFILE_PARAMETER_RETURNS] = false;
                # existsFields[POINTCLOUDFILE_PARAMETER_SOURCE_ID] = false;
                # existsFields[POINTCLOUDFILE_PARAMETER_USER_DATA] = false;
                existsFieldsByTileDict = ret[4] # QMap<int,QMap<int,QMap<QString,bool> > >

                filesIdByTileDict = ret[5] # QMap<int,QMap<int,QVector<int> > >

                numberOfTiles = 0
                for tileX in tilesNames:
                    for tileY in tilesNames[tileX]:
                        numberOfTiles = numberOfTiles + 1
                progress = QProgressDialog(self.iface.mainWindow())
                progress.setCancelButton(None)
                progress.setMinimumDuration(0)
                progress.setRange(0, numberOfTiles)
                progress.setWindowModality(Qt.WindowModal)
                progress.setWindowTitle('Creating tiles virtual layers ...')
                progress.show()
                fieldsByTileTableName = {}
                i = 0
                for tileX in tilesNames:
                    for tileY in tilesNames[tileX]:
                        tileName = tilesNames[tileX][tileY]
                        i = i + 1
                        labelText = 'Creating ' + str(numberOfTiles) +' tiles virtual layers ...'
                        labelText += '\nCreating ' + tileName + ',' + str(i) + '/' + str(numberOfTiles)
                        progress.setLabelText(labelText)
                        progress.setValue(i)
                        layerList = QgsProject.instance().mapLayersByName(tileName)
                        if layerList:
                            continue
                        fieldsByTileTableName[tileName] = []
                        layerParameters = "Point?crs=EPSG:" + str(projectCrsEpsgCode)
                        layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_FILE_ID+":integer"
                        layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_POSITION+":integer"
                        layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW+":integer(2)"
                        layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS+":integer(2)"
                        layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_ALTITUDE+":double"
                        # layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_REMOVED+":integer(1)"
                        fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_POSITION)
                        fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW)
                        fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS)
                        fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_ALTITUDE)
                        # fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_REMOVED)
                        if existsFieldsByTileDict[tileX][tileY][qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_GPS_TIME]:
                            layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_GPS_TIME+":double"
                            fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_GPS_TIME)
                        if existsFieldsByTileDict[tileX][tileY][qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_USER_DATA]:
                            layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_USER_DATA+":integer(2)"
                            fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_USER_DATA)
                        if existsFieldsByTileDict[tileX][tileY][qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_INTENSITY]:
                            layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_INTENSITY+":integer(2)"
                            fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_INTENSITY)
                        if existsFieldsByTileDict[tileX][tileY][qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_SOURCE_ID]:
                            layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_SOURCE_ID+":integer(2)"
                            fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_SOURCE_ID)
                        if existsFieldsByTileDict[tileX][tileY][qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURN]:
                            layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_RETURN+":integer(2)"
                            fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_RETURN)
                        if existsFieldsByTileDict[tileX][tileY][qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURNS]:
                            layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_RETURNS+":integer(2)"
                            fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURNS)
                        if existsFieldsByTileDict[tileX][tileY][qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_NIR]:
                            layerParameters += "&field="+qLidarDefinitions.CONST_TILE_FIELD_NAME_NIR+":integer(2)"
                            fieldsByTileTableName[tileName].append(qLidarDefinitions.CONST_TILE_FIELD_NAME_NIR)
                        vlayer = QgsVectorLayer(layerParameters,tileName, "memory")
                        if vlayer.isValid():
                            # if vlayer.featureCount() == 0:
                            #     return
                            QgsProject.instance().addMapLayer(vlayer, False)
                            self.layerTreePCTiles.insertChildNode(1, QgsLayerTreeLayer(vlayer))
                            # vlayer.loadNamedStyle(self.qmlPointCloudFileName)
                            # vlayer.triggerRepaint()
                            # self.iface.setActiveLayer(vlayer)
                            # self.iface.zoomToActiveLayer()
                            self.loadedTiles.append(tileName)
                        else:
                            msgBox = QMessageBox(self)
                            msgBox.setIcon(QMessageBox.Information)
                            msgBox.setWindowTitle(self.windowTitle)
                            msgBox.setText("Impossible to Load table: " + tileName
                                           + " into QGIS")
                            msgBox.exec_()
                        provider = vlayer.dataProvider()
                        fields = provider.fields()
                        filesId = filesIdByTileDict[tileX][tileY]
                        featuresInTile = []
                        for fileId in filesId:
                            if not fileId in pointsByTileByFileId:
                                break
                            pointsByTile = pointsByTileByFileId[fileId]
                            exitsFields = {}
                            if fileId in existsFieldsByFileId:
                                exitsFields = existsFieldsByFileId[fileId]
                            if not tileX in pointsByTile:
                                break;
                            if not tileY in pointsByTile[tileX]:
                                break;
                            points = pointsByTile[tileX][tileY]
                            for pto in points:
                                ix = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_IX]
                                ptoFc = tileX + ix / 1000.
                                iy = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_IY]
                                ptoSc = tileY + iy / 1000.
                                ptoPosition = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_POSITION]
                                ptoClass = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_CLASS]
                                ptoClassNew = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_CLASS_NEW]
                                # ptoRemoved = 0
                                # if ptoClassNew == qLidarDefinitions.CONST_CLASS_NUMBER_REMOVE:
                                #     ptoRemoved = 1
                                ptoTc = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_Z]
                                pto8bits = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_VALUES_8BITS]
                                pto16bits = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_VALUES_16BITS]
                                ptoFeature = QgsFeature()
                                ptoCoordinates = QgsPointXY()
                                ptoCoordinates.setX(ptoFc)
                                ptoCoordinates.setY(ptoSc)
                                ptoGeometry = QgsGeometry.fromPointXY(ptoCoordinates)
                                ptoFeature.setGeometry(ptoGeometry)
                                ptoFeature.setFields(fields)
                                ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_FILE_ID,fileId)
                                ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_POSITION,ptoPosition)
                                ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW,ptoClassNew)
                                ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS,ptoClass)
                                ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_ALTITUDE,ptoTc)
                                if exitsFields[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_GPS_TIME]:
                                    ptoGpsTime = pto[qLidarDefinitions.CONST_POINTCLOUDFILE_PYTHON_TAG_GPS_TIME]
                                    ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_GPS_TIME, ptoGpsTime)
                                if exitsFields[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_USER_DATA]:
                                    if qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_USER_DATA in pto8bits:
                                        ptoUserData = pto8bits[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_USER_DATA]
                                        ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_USER_DATA, ptoUserData)
                                if exitsFields[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_INTENSITY]:
                                    if qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_INTENSITY in pto16bits:
                                        ptoIntensity = pto16bits[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_INTENSITY]
                                        ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_INTENSITY, ptoIntensity)
                                if exitsFields[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_SOURCE_ID]:
                                    if qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_SOURCE_ID in pto16bits:
                                        ptoSourceId = pto16bits[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_SOURCE_ID]
                                        ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_SOURCE_ID, ptoSourceId)
                                if exitsFields[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURN]:
                                    if qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURN in pto8bits:
                                        ptoReturn = pto8bits[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURN]
                                        ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_RETURN, ptoReturn)
                                if exitsFields[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURNS]:
                                    if qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURNS in pto8bits:
                                        ptoReturns = pto8bits[qLidarDefinitions.CONST_POINTCLOUDFILE_PARAMETER_RETURNS]
                                        ptoFeature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_RETURNS, ptoReturns)
                                featuresInTile.append(ptoFeature)
                        if len(featuresInTile) > 0:
                            provider.addFeatures(featuresInTile)
                            vlayer.updateExtents()
                            vlayer.loadNamedStyle(self.qmlPointCloudFileName)
                            vlayer.setScaleBasedVisibility(True)
                            vlayer.setMinimumScale(self.minimumScale)
                            vlayer.setMaximumScale(qLidarDefinitions.CONST_MAXIMUM_SCALE)
                            vlayer.triggerRepaint()
                progress.close()
        self.toolButton_SelectByRectangle.setEnabled(True)
        self.toolButton_SelectByPolygon.setEnabled(True)
        self.toolButton_SelectByFreehand.setEnabled(True)
        # msgBox = QMessageBox(self)
        # msgBox.setIcon(QMessageBox.Information)
        # msgBox.setWindowTitle(self.windowTitle)
        # msgBox.setText("Minimum scale: 1/" + str(self.minimumScale))
        # msgBox.exec_()
        # En el initialize updateScales(self, scales: Iterable[str] = [])
        self.iface.mapCanvas().zoomScale(self.minimumScale-1)
        posInScaleComboBox = self.scales.index(self.minimumScale)
        self.minScaleComboBox.currentIndexChanged.disconnect(self.selectMinScale)
        self.minScaleComboBox.setCurrentIndex(posInScaleComboBox)
        self.minScaleComboBox.currentIndexChanged.connect(self.selectMinScale)
        self.actionSetVisiblePoints()
        return

    def selectNewProjectPath(self):
        oldFileName=self.projectPathLineEdit.text()
        title="Select New Project Path"
        strDir = QFileDialog.getExistingDirectory(self,title,self.path,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if strDir:
            if not len(QDir(strDir).entryList(QDir.NoDotAndDotDot|QDir.AllEntries)) == 0:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Select the path of an empty folder ")
                msgBox.exec_()
                # self.projectPathLineEdit.setText('')
                return
            self.path = strDir
            self.projectPathLineEdit.setText(strDir)
            self.settings.setValue("last_path", self.path)
            self.settings.sync()
        return

    def selectProjectParameters(self):
        projectType = self.projectTypeComboBox.currentText()
        if projectType == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select project type before")
            msgBox.exec_()
            return
        ret = self.iPyProject.pctSelectProjectParameters(projectType)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
        return

    def selectPCFs(self):
        previousFiles = self.pointCloudFiles[:] # copia desligada
        dlg = MultipleFileSelectorDialog(self.iface,
                                         self.path,
                                         qLidarDefinitions.CONST_SELECT_POINT_CLOUD_FILES_DIALOG_TITLE,
                                         self.pointCloudFilesFileTypes,
                                         self.pointCloudFiles,
                                         self.pointCloudFilesActiveFileExtensions)
        dlg.show() # show the dialog
        result = dlg.exec_() # Run the dialog
        self.path = dlg.getPath()
        self.settings.setValue("last_path",self.path)
        files = dlg.getFiles() # los hay repetidos
        self.pointCloudFiles = []
        self.numberOfPCFsLineEdit.setText("0")
        for file in files:
            fileBaseName = QFileInfo(file).baseName()
            findFile = False
            for pointCloudFile in self.pointCloudFiles:
                if fileBaseName == QFileInfo(pointCloudFile).baseName():
                    findFile = True
                    break
            if not findFile:
                self.pointCloudFiles.append(file)
        self.pointCloudFilesActiveFileExtensions = dlg.getActiveFileExtensions()
        self.numberOfPCFsLineEdit.setText(str(len(self.pointCloudFiles)))
        return

    def selectPostprocessingIPCFs(self):
        previousFiles = self.postprocessingIPCFs[:] # copia desligada
        dlg = MultipleFileSelectorDialog(self.iface,
                                         self.path,
                                         qLidarDefinitions.CONST_SELECT_POINT_CLOUD_FILES_DIALOG_TITLE,
                                         self.pointCloudFilesFileTypes,
                                         self.postprocessingIPCFs,
                                         self.pointCloudFilesActiveFileExtensions)
        dlg.show() # show the dialog
        result = dlg.exec_() # Run the dialog
        self.path = dlg.getPath()
        self.settings.setValue("last_path",self.path)
        files = dlg.getFiles() # los hay repetidos
        self.postprocessingIPCFs = []
        self.numberOfPCFsLineEdit.setText("0")
        for file in files:
            fileBaseName = QFileInfo(file).baseName()
            findFile = False
            for pointCloudFile in self.postprocessingIPCFs:
                if fileBaseName == QFileInfo(pointCloudFile).baseName():
                    findFile = True
                    break
            if not findFile:
                self.postprocessingIPCFs.append(file)
        self.pointCloudFilesActiveFileExtensions = dlg.getActiveFileExtensions()
        self.ppToolsNumberOfIPCFsLineEdit.setText(str(len(self.postprocessingIPCFs)))
        return

    def selectPpToolsOutputFile(self):
        oldFileName=self.ppToolsOPCFsOutputFileLineEdit.text()
        title="Select preprocessing tools output file"
        filters="Point Cloud File, Image File, Txt File (*."
        cont = 0
        for fileType in self.pointCloudFilesFileTypes:
            filters+=fileType
            cont = cont + 1
            if cont < len(self.pointCloudFilesFileTypes):
                filters+=";*."
        filters += ";*.tif"
        filters += ";*.txt"
        filters += ";*.shp"
        filters += ";*.kml"
        filters += ";*.wkt"
        filters+=")"
        fileName, _ = QFileDialog.getSaveFileName(self,title,self.path,filters)
        if fileName:
            fileInfo = QFileInfo(fileName)
            self.path = fileInfo.absolutePath()
            self.ppToolsOPCFsOutputFileLineEdit.setText(fileName)
            self.settings.setValue("last_path", self.path)
            self.settings.sync()
        return

    def selectPpToolsOutpufFilesPrefix(self):
        oldText = self.ppToolsOPCFsPrefixLineEdit.text()
        label = "Input prefix for output preprocessed point cloud files:"
        title = qLidarDefinitions.CONST_PROGRAM_TITLE
        [text, ok] = QInputDialog.getText(self, title, label, QLineEdit.Normal, oldText)
        if ok and text:
            text = text.strip()
            if not text == oldText:
                self.ppToolsOPCFsPrefixLineEdit.setText(text)
        return

    def selectPpToolsOutpufFilesSuffix(self):
        oldText = self.ppToolsOPCFsSuffixLineEdit.text()
        label = "Input suffix for output preprocessed point cloud files:"
        title = qLidarDefinitions.CONST_PROGRAM_TITLE
        [text, ok] = QInputDialog.getText(self, title, label, QLineEdit.Normal, oldText)
        if ok and text:
            text = text.strip()
            if not text == oldText:
                self.ppToolsOPCFsSuffixLineEdit.setText(text)
        return

    def selectPpToolsOutputPath(self):
        strDir = QFileDialog.getExistingDirectory(self,"Select directory",self.path,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if strDir:
            self.settings.setValue("lasttools_path", strDir)
            self.settings.sync()
            self.ppToolsOPCFsOutputPathLineEdit.setText(strDir)
        return

    def selectProjectManagerOutputPath(self):
        strDir = QFileDialog.getExistingDirectory(self,"Select directory", self.projectManagerOutputPath,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if strDir:
            ret = self.iPyProject.pctSetProjectManagerOutputPath(self.projectManagerOutputPath)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n" + ret[1])
                msgBox.exec_()
                self.pmOutputPathLineEdit.setText("")
                self.projectManagerOutputPath = None
                return
            self.projectManagerOutputPath = strDir
            self.settings.setValue("project_management_output_path", self.projectManagerOutputPath)
            self.settings.sync()
            self.pmOutputPathLineEdit.setText(strDir)
        return

    def selectProjectManagerTemporalPath(self):
        strDir = QFileDialog.getExistingDirectory(self,"Select directory", self.projectManagerTemporalPath,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if strDir:
            ret = self.iPyProject.pctSetProjectManagerTemporalPath(self.projectManagerTemporalPath)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n" + ret[1])
                msgBox.exec_()
                self.pmTemporalPathLineEdit.setText("")
                self.projectManagerTemporalPath = None
                return
            self.projectManagerTemporalPath = strDir
            self.settings.setValue("project_management_temporal_path", self.projectManagerTemporalPath)
            self.settings.sync()
            self.pmTemporalPathLineEdit.setText(strDir)
        return

    def selectProject(self):
        self.openProjectPushButton.setEnabled(False)
        self.closeProjectPushButton.setEnabled(False)
        self.removeProjectPushButton.setEnabled(False)
        projectFilePath = self.projectsComboBox.currentText()
        if projectFilePath == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            self.projectManagementTabWidget.setEnabled(True)
            self.projectManagementTabWidget.setTabEnabled(0, True)
            self.projectManagementTabWidget.setTabEnabled(1, False)
            self.projectManagementTabWidget.setTabEnabled(2, False)
            self.projectManagementTabWidget.setCurrentIndex(0)
            if self.projectPath:
                self.closeProject()
        else:
            self.projectManagementTabWidget.setEnabled(False)
            # self.projectManagementTabWidget.setTabEnabled(0, False)
            # self.projectManagementTabWidget.setTabEnabled(1, False)
            # self.projectManagementTabWidget.setTabEnabled(2, False)
            self.projectManagementTabWidget.setCurrentIndex(1)
            self.openProjectPushButton.setEnabled(True)
            self.closeProjectPushButton.setEnabled(False)
            self.removeProjectPushButton.setEnabled(True)
        # if self.connectionFileName:
        #     self.openProject()
        return

    def selectProjectType(self):
        # projectType = self.projectTypeComboBox.currentText()
        # # msgBox = QMessageBox(self)
        # # msgBox.setIcon(QMessageBox.Information)
        # # msgBox.setWindowTitle(self.windowTitle)
        # # msgBox.setText("Project type: "+projectType)
        # # msgBox.exec_()
        return

    def selectReclassificationConfusionMatrixReportProcess(self):
        outputFile = self.reclassificationConfusionMatrixReportOutputFileLineEdit.text()
        if not outputFile:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select output file")
            msgBox.exec_()
            return
        selectedClasses = self.reclassificationConfusionMatrixReportValidSelectClasses
        if self.reclassificationConfussionMatrixReportSelectedClassesRadioButton.isChecked():
            selectedClasses = []
            strSelectedClasses = self.reclassificationConfusionMatrixReportSelectClassesLineEdit.text()
            values = strSelectedClasses.split(';')
            for selectedClass in values:
                selectedClasses.append(int(selectedClass))
        ret = self.iPyProject.pctProcessReclassificationConfusionMatrixReport(self.projectPath,
                                                                              selectedClasses,
                                                                              outputFile)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            # self.projectsComboBox.setCurrentIndex(0)
            return
        else:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Process completed successfully")
            msgBox.exec_()
        return

    def selectReclassificationConfusionMatrixSelectClasses(self):
        oldValue = self.reclassificationConfusionMatrixReportSelectClassesLineEdit.text()
        text, ok = QInputDialog.getText(self, 'Input selected classes', 'Selected classes, (integers separated by ;):',QLineEdit.Normal,oldValue)
        if ok:
            values = text.split(';')
            validSelectedClasses = []
            for selectedClass in values:
                if not selectedClass.isdigit():
                    continue
                value = int(selectedClass)
                if value in validSelectedClasses:
                    continue
                if not value in self.reclassificationConfusionMatrixReportValidSelectClasses:
                    continue
                validSelectedClasses.append(selectedClass)
            if len(validSelectedClasses) < 1:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Invalid selection")
                msgBox.exec_()
                return
            newValue = ''
            cont = 0
            for validSelectedClass in validSelectedClasses:
                newValue += str(validSelectedClass)
                cont = cont + 1
                if cont<len(validSelectedClasses):
                    newValue += ';'
            self.reclassificationConfusionMatrixReportSelectClassesLineEdit.setText(newValue)
        return

    def selectReclassificationConfusionMatrixReportFile(self):
        oldFileName = self.reclassificationConfusionMatrixReportOutputFileLineEdit.text()
        title="Select reclassification confusion matrix report file"
        filters="Txt (*.txt)"
        fileName, _ = QFileDialog.getSaveFileName(self,title,self.path,filters)
        if fileName:
            fileInfo = QFileInfo(fileName)
            self.path = fileInfo.absolutePath()
            self.reclassificationConfusionMatrixReportOutputFileLineEdit.setText(fileName)
            self.settings.setValue("last_path", self.path)
            self.settings.sync()
        return

    def selectReclassificationConfusionMatrixSelectedClasses(self):
        if self.reclassificationConfussionMatrixReportSelectedClassesRadioButton.isChecked():
            self.reclassificationConfusionMatrixReportSelectClassesLineEdit.setEnabled(True)
            self.reclassificationConfusionMatrixReportSelectClassesPushButton.setEnabled(True)
        else:
            self.reclassificationConfusionMatrixReportSelectClassesLineEdit.setEnabled(False)
            self.reclassificationConfusionMatrixReportSelectClassesPushButton.setEnabled(False)
        return

    def selectReclassificationConfusionMatrixReportAllClasses(self):
        if self.reclassificationConfussionMatrixReportSelectedClassesRadioButton.isChecked():
            self.reclassificationConfusionMatrixReportSelectClassesLineEdit.setEnabled(True)
            self.reclassificationConfusionMatrixReportSelectClassesPushButton.setEnabled(True)
        else:
            self.reclassificationConfusionMatrixReportSelectClassesLineEdit.setEnabled(False)
            self.reclassificationConfusionMatrixReportSelectClassesPushButton.setEnabled(False)
        return

    def selectRois(self):
        previousFiles = self.roisShapefiles[:] # copia desligada
        dlg = MultipleFileSelectorDialog(self.iface,
                                         self.path,
                                         qLidarDefinitions.CONST_SELECT_ROIS_SHAPEFILES_DIALOG_TITLE,
                                         self.roisFileTypes,
                                         self.roisShapefiles,
                                         self.roisFilesActiveFileExtensions)
        dlg.show() # show the dialog
        result = dlg.exec_() # Run the dialog
        self.path = dlg.getPath()
        self.settings.setValue("last_path",self.path)
        self.settings.sync()
        files = dlg.getFiles() # los hay repetidos
        self.roisShapefiles = []
        self.numberOfRoisLineEdit.setText("0")
        for file in files:
            fileBaseName = QFileInfo(file).baseName()
            findFile = False
            for roiFile in self.roisShapefiles:
                if fileBaseName == QFileInfo(roiFile).baseName():
                    findFile = True
                    break
            if not findFile:
                self.roisShapefiles.append(file)
        self.roisFilesActiveFileExtensions = dlg.getActiveFileExtensions()
        self.numberOfRoisLineEdit.setText(str(len(self.roisShapefiles)))
        return

    def setCrs(self):
        crs = self.projectQgsProjectionSelectionWidget.crs()
        isValidCrs = crs.isValid()
        crsAuthId = crs.authid()
        if not "EPSG:" in crsAuthId:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not EPSG")
            msgBox.exec_()
            self.projectQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        crsEpsgCode = int(crsAuthId.replace('EPSG:',''))
        crsOsr = osr.SpatialReference()  # define test1
        if crsOsr.ImportFromEPSG(crsEpsgCode) != 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error importing OSR CRS from EPSG code" + str(crsEpsgCode))
            msgBox.exec_()
            self.projectQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        if not crsOsr.IsProjected():
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not a projected CRS")
            msgBox.exec_()
            self.projectQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        self.setVerticalCRSs(crsEpsgCode)
        crsEpsgCodeString = 'EPSG:'+str(crsEpsgCode)
        # self.addPCFsQgsProjectionSelectionWidget.setCrs(
        #     QgsCoordinateReferenceSystem(crsEpsgCodeString))
        self.crsEpsgCode = crsEpsgCode

    def setCrsAddPCFs(self):
        crs = self.addPCFsQgsProjectionSelectionWidget.crs()
        isValidCrs = crs.isValid()
        crsAuthId = crs.authid()
        if not "EPSG:" in crsAuthId:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not EPSG")
            msgBox.exec_()
            self.addPCFsQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        crsEpsgCode = int(crsAuthId.replace('EPSG:',''))
        crsOsr = osr.SpatialReference()  # define test1
        if crsOsr.ImportFromEPSG(crsEpsgCode) != 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error importing OSR CRS from EPSG code" + str(crsEpsgCode))
            msgBox.exec_()
            self.addPCFsQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        if not crsOsr.IsProjected() and not crsOsr.IsGeographic():
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not a projected or geographic CRS")
            msgBox.exec_()
            self.addPCFsQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        self.setVerticalCRSsAddPCFs(crsEpsgCode)

    def setCrsPpToolsIPCFs(self):
        crs = self.ppToolsIPCFsQgsProjectionSelectionWidget.crs()
        isValidCrs = crs.isValid()
        crsAuthId = crs.authid()
        if not "EPSG:" in crsAuthId:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not EPSG")
            msgBox.exec_()
            self.ppToolsIPCFsQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        crsEpsgCode = int(crsAuthId.replace('EPSG:',''))
        crsOsr = osr.SpatialReference()  # define test1
        if crsOsr.ImportFromEPSG(crsEpsgCode) != 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error importing OSR CRS from EPSG code" + str(crsEpsgCode))
            msgBox.exec_()
            self.ppToolsIPCFsQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        if not crsOsr.IsProjected() and not crsOsr.IsGeographic():
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Selected CRS is not a projected or geographic CRS")
            msgBox.exec_()
            self.ppToolsIPCFsQgsProjectionSelectionWidget.setCrs(
                QgsCoordinateReferenceSystem(qLidarDefinitions.CONST_DEFAULT_CRS))
            return
        self.setVerticalCRSsPpToolsIPCFs(crsEpsgCode)

    def setVerticalCRSs(self,crsEpsgCode):
        self.verticalCRSsComboBox.clear()
        self.verticalCRSsComboBox.addItem(qLidarDefinitions.CONST_ELLIPSOID_HEIGHT)
        ret = self.iPyProject.getVerticalCRSs(crsEpsgCode)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            # self.projectsComboBox.setCurrentIndex(0)
            return
        else:
            cont = 0
            for value in ret:
                if cont > 0:
                    # strCrs = qLidarDefinitions.CONST_EPSG_PREFIX + str(value)
                    self.verticalCRSsComboBox.addItem(value)
                cont = cont + 1
            # msgBox = QMessageBox(self)
            # msgBox.setIcon(QMessageBox.Information)
            # msgBox.setWindowTitle(self.windowTitle)
            # msgBox.setText("Process completed successfully")
            # msgBox.exec_()
        strCrs = qLidarDefinitions.CONST_EPSG_PREFIX + str(crsEpsgCode)
        if strCrs == qLidarDefinitions.CONST_DEFAULT_CRS:
            index = self.verticalCRSsComboBox.findText(qLidarDefinitions.CONST_DEFAULT_VERTICAL_CRS)#, QtCore.Qt.MatchFixedString)
            if index > 0:
                self.verticalCRSsComboBox.setCurrentIndex(index)
        return

    def setVerticalCRSsAddPCFs(self,crsEpsgCode):
        self.addPCFsVerticalCRSsComboBox.clear()
        self.addPCFsVerticalCRSsComboBox.addItem(qLidarDefinitions.CONST_ELLIPSOID_HEIGHT)
        ret = self.iPyProject.getVerticalCRSs(crsEpsgCode)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            # self.projectsComboBox.setCurrentIndex(0)
            return
        else:
            cont = 0
            for value in ret:
                if cont > 0:
                    # strCrs = qLidarDefinitions.CONST_EPSG_PREFIX + str(value)
                    self.addPCFsVerticalCRSsComboBox.addItem(value)
                cont = cont + 1
            # msgBox = QMessageBox(self)
            # msgBox.setIcon(QMessageBox.Information)
            # msgBox.setWindowTitle(self.windowTitle)
            # msgBox.setText("Process completed successfully")
            # msgBox.exec_()
        strCrs = qLidarDefinitions.CONST_EPSG_PREFIX + str(crsEpsgCode)
        if strCrs == qLidarDefinitions.CONST_DEFAULT_CRS:
            index = self.addPCFsVerticalCRSsComboBox.findText(qLidarDefinitions.CONST_DEFAULT_VERTICAL_CRS)#, QtCore.Qt.MatchFixedString)
            if index > 0:
                self.addPCFsVerticalCRSsComboBox.setCurrentIndex(index)
        return

    def setVerticalCRSsPpToolsIPCFs(self,crsEpsgCode):
        self.ppToolsIPCFsVerticalCRSsComboBox.clear()
        self.ppToolsIPCFsVerticalCRSsComboBox.addItem(qLidarDefinitions.CONST_ELLIPSOID_HEIGHT)
        ret = self.iPyProject.getVerticalCRSs(crsEpsgCode)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            # self.projectsComboBox.setCurrentIndex(0)
            return
        else:
            cont = 0
            for value in ret:
                if cont > 0:
                    # strCrs = qLidarDefinitions.CONST_EPSG_PREFIX + str(value)
                    self.ppToolsIPCFsVerticalCRSsComboBox.addItem(value)
                cont = cont + 1
            # msgBox = QMessageBox(self)
            # msgBox.setIcon(QMessageBox.Information)
            # msgBox.setWindowTitle(self.windowTitle)
            # msgBox.setText("Process completed successfully")
            # msgBox.exec_()
        strCrs = qLidarDefinitions.CONST_EPSG_PREFIX + str(crsEpsgCode)
        if strCrs == qLidarDefinitions.CONST_DEFAULT_CRS:
            index = self.ppToolsIPCFsVerticalCRSsComboBox.findText(qLidarDefinitions.CONST_DEFAULT_VERTICAL_CRS)#, QtCore.Qt.MatchFixedString)
            if index > 0:
                self.ppToolsIPCFsVerticalCRSsComboBox.setCurrentIndex(index)
        return

    def showAboutDlg(self):
        if self.about_qdialog == None:
            self.about_qdialog = AboutQDialog()
        self.about_qdialog.show()

    def toClass0(self):
        newClass = 0
        self.actionWithSelectedPoints(newClass)
        return

    def toClass1(self):
        newClass = 1
        self.actionWithSelectedPoints(newClass)
        return

    def toClass12(self):
        newClass = 12
        self.actionWithSelectedPoints(newClass)
        return

    def toClass2(self):
        newClass = 2
        self.actionWithSelectedPoints(newClass)
        return

    def toClass3(self):
        newClass = 3
        self.actionWithSelectedPoints(newClass)
        return

    def toClass4(self):
        newClass = 4
        self.actionWithSelectedPoints(newClass)
        return

    def toClass5(self):
        newClass = 5
        self.actionWithSelectedPoints(newClass)
        return

    def toClass6(self):
        newClass = 6
        self.actionWithSelectedPoints(newClass)
        return

    def toClass7(self):
        newClass = 7
        self.actionWithSelectedPoints(newClass)
        return

    def toClass9(self):
        newClass = 9
        self.actionWithSelectedPoints(newClass)
        return

    def removeProject(self):
        projectPath=self.projectsComboBox.currentText()
        if projectPath == qLidarDefinitions.CONST_NO_COMBO_SELECT:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Select project to remove from list")
            msgBox.exec_()
            return
        self.projects.remove(projectPath)
        strProjects = ""
        cont = 0
        for project in self.projects:
            if cont > 0:
                strProjects = strProjects + qLidarDefinitions.CONST_PROJECTS_STRING_SEPARATOR
            strProjects += project
            cont = cont + 1
        self.settings.setValue("projects", strProjects)
        self.settings.sync()
        self.projectsComboBox.currentIndexChanged.disconnect(self.selectProject)
        self.projectsComboBox.clear()
        self.projectsComboBox.addItem(qLidarDefinitions.CONST_NO_COMBO_SELECT)
        for project in self.projects:
            self.projectsComboBox.addItem(project)
        self.projectsComboBox.currentIndexChanged.connect(self.selectProject)
        self.projectsComboBox.setCurrentIndex(0)
        self.projectManagementTabWidget.setEnabled(True)
        self.projectManagementTabWidget.setTabEnabled(0, True)
        self.projectManagementTabWidget.setTabEnabled(1, False)
        self.projectManagementTabWidget.setTabEnabled(2, False)
        self.projectManagementTabWidget.setCurrentIndex(0)
        return

    def runProcessList(self):
        if self.ppToolsTabWidget.currentIndex() == 0:
            if len(self.processList) == 0:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Process list is empty")
                msgBox.exec_()
                return
            title = qLidarDefinitions.CONST_RUN_PROCESS_LIST_DIALOG_TITLE
            ret = self.iPyProject.pctRunProcessList(self.processList, title)
        elif self.ppToolsTabWidget.currentIndex() == 1:
            command = self.ppToolsInternalCommandComboBox.currentText()
            if command == qLidarDefinitions.CONST_NO_COMBO_SELECT:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Select internal command before")
                msgBox.exec_()
                return
            crs = self.ppToolsIPCFsQgsProjectionSelectionWidget.crs()
            isValidCrs = crs.isValid()
            crsAuthId = crs.authid()
            if not "EPSG:" in crsAuthId:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Selected CRS is not EPSG")
                msgBox.exec_()
                return
            crsEpsgCode = int(crsAuthId.replace('EPSG:', ''))
            crsOsr = osr.SpatialReference()  # define test1
            if crsOsr.ImportFromEPSG(crsEpsgCode) != 0:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error importing OSR CRS from EPSG code" + str(crsEpsgCode))
                msgBox.exec_()
                return
            if not crsOsr.IsProjected():
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Selected CRS is not a projected CRS")
                msgBox.exec_()
                return
            altitudeIsMsl = True
            verticalCrsEpsgCode = -1
            if self.projVersionMajor < 8:
                if self.ppToolsIPCFsAltitudeEllipsoidRadioButton.isChecked():
                    altitudeIsMsl = False
            else:
                verticalCrsStr = self.ppToolsIPCFsVerticalCRSsComboBox.currentText()
                if not verticalCrsStr == qLidarDefinitions.CONST_ELLIPSOID_HEIGHT:
                    verticalCrsEpsgCode = int(verticalCrsStr.replace('EPSG:', ''))
            inputFiles = self.postprocessingIPCFs
            if len(inputFiles) == 0:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Select input files")
                msgBox.exec_()
                return
            outputFile = self.ppToolsOPCFsOutputFileLineEdit.text()
            outputPath = self.ppToolsOPCFsOutputPathLineEdit.text()
            suffixOutputFiles = self.ppToolsOPCFsSuffixLineEdit.text()
            prefixOutputFiles = self.ppToolsOPCFsPrefixLineEdit.text()
            # ??se puede ignorar para algunos procesos si hay varios ficheros de entrada? lasmerge ...
            # tengo que definir en un contenedor aquellos comandos que lo permiten
            # if len(inputFiles) > 1 and outputFile:
            #     if self.ppToolsOPCFsOutputPathPushButton.isEnabled():
            #         if not outputPath and not suffixOutputFiles:
            #             msgBox = QMessageBox(self)
            #             msgBox.setIcon(QMessageBox.Information)
            #             msgBox.setWindowTitle(self.windowTitle)
            #             msgBox.setText("Select output path or suffix for several input files")
            #             msgBox.exec_()
            #             return
            # if not outputFile and not outputPath and not suffixOutputFiles:
            if not outputFile and not outputPath:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Select output file or output path")
                msgBox.exec_()
                return
            ret = self.iPyProject.pctProcessInternalCommand(command,
                                                            inputFiles,
                                                            outputPath,
                                                            outputFile,
                                                            suffixOutputFiles,
                                                            prefixOutputFiles)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n"+ret[1])
                msgBox.exec_()
                return
            else:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Process completed successfully")
                msgBox.exec_()
            return
        return

    def selectAllClasses(self):
        newClass = qLidarDefinitions.CONST_ACTION_ALL_CLASSES_VALUE
        self.actionWithSelectedPoints(newClass)
        return

    def toOriginalClass(self):
        self.allClassesPushButton.setEnabled(True)
        return

    def unenableAllClasses(self):
        self.allClassesPushButton.setEnabled(False)
        return

    def unloadAllTiles(self):
        if self.layerTreePCTiles:
            root = QgsProject.instance().layerTreeRoot()
            self.layerTreeProject = root.findGroup(self.layerTreeProjectName)
            if not self.layerTreeProject:
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Layers group: " + self.layerTreeProjectName
                               + " not found\nClose and reload the project")
                msgBox.exec_()
                return
            projectRoot = self.layerTreeProject
            self.removeGroup(projectRoot,self.layerTreePCTilesName)
            self.layerTreePCTiles = None
            self.layerTreePCTilesName = None
            self.loadedTiles = []
            self.iface.mapCanvas().refresh()
            self.toolButton_SelectByRectangle.setEnabled(False)
            self.toolButton_SelectByPolygon.setEnabled(False)
            self.toolButton_SelectByFreehand.setEnabled(False)
            posInScaleComboBox = self.scales.index(self.minimumScale)
            self.minScaleComboBox.currentIndexChanged.disconnect(self.selectMinScale)
            self.minScaleComboBox.setCurrentIndex(posInScaleComboBox)
            self.minScaleComboBox.currentIndexChanged.connect(self.selectMinScale)
        return

    def updateClassesWithoutEditing(self):
        changedPoints,changedTileNames = self.getChangedPoints() # tile_name,fileId,pos,classNew,class
        if len(changedPoints) == 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("There are no changes to update")
            msgBox.exec_()
            return
        ret = self.iPyProject.pctUpdateNotEdited2dToolsPoints(self.projectPath,
                                                              changedPoints)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n" + ret[1])
            msgBox.exec_()
            return
        else:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Point classes have been updated " )
            msgBox.exec_()
            return
        return

    def view3D(self,
               wktGeometry,
               loadFullTiles):
        projectCrs = QgsProject.instance().crs()
        projectCrsEpsgCode = -1
        projectCrsProj4 = ""
        projectCrsAuthId = projectCrs.authid()
        if "EPSG" in projectCrsAuthId:
            projectCrsEpsgCode = int(projectCrsAuthId.replace("EPSG:",""))
        projectCrsProj4 = projectCrs.toProj4()
        # mapCanvasCrsEpsgCode = int(self.iface.mapCanvas().mapRenderer().destinationCrs().authid().replace("EPSG:",""))
        # mapCanvasCrs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        ret = self.iPyProject.pctView3dFromWktGeometry(self.projectPath,
                                                       wktGeometry,
                                                       projectCrsEpsgCode,
                                                       projectCrsProj4,
                                                       loadFullTiles,
                                                       self.loadedTiles)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n"+ret[1])
            msgBox.exec_()
            return
        if len(self.loadedTiles) == 0:
            return
        updatedPointsByTileName = ret[1]
        numberOfTiles = len(updatedPointsByTileName)
        progress = QProgressDialog(self.iface.mainWindow())
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setRange(0, numberOfTiles)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle('Recovering changes')
        progress.show()
        nTile = 0
        for tileName in updatedPointsByTileName:
            nTile = nTile + 1
            labelText = 'Recovering changes for ' + str(numberOfTiles) +' tiles ...'
            labelText += '\nUpdating ' + tileName + ',' + str(nTile) + '/' + str(numberOfTiles)
            progress.setLabelText(labelText)
            progress.setValue(nTile)
            layers = QgsProject.instance().mapLayersByName(tileName)
            if len(layers) != 1:
                continue
            layer = layers[0]
            if layer.type() != QgsMapLayer.VectorLayer:
                continue
            layerInEdition = False
            updatedPoints = updatedPointsByTileName[tileName]
            updatedPointsFileIdAndPositionInTile = []
            updatedPointsClassNew = []
            for i in range(len(updatedPoints)):
                fileIdAndPositionInTile = str(updatedPoints[i][0]) + '_' + str(updatedPoints[i][1])
                updatedPointsFileIdAndPositionInTile.append(fileIdAndPositionInTile)
                updatedPointsClassNew.append(updatedPoints[i][2])
            layer.selectAll()
            features = layer.selectedFeatures()
            existsChanges = False
            progressFeatures = QProgressDialog(self.iface.mainWindow())
            progressFeatures.setCancelButton(None)
            progressFeatures.setMinimumDuration(0)
            progressFeatures.setRange(0, len(features))
            progressFeatures.setWindowModality(Qt.WindowModal)
            progressFeatures.setWindowTitle('Recovering changes')
            progressFeatures.setLabelText('Recovering changes for ' + str(len(features)) + ' features ...')
            progressFeatures.show()
            nFeature = 0
            for feature in features:
                nFeature = nFeature + 1
                progressFeatures.setValue(nFeature)
                featureFileId = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_FILE_ID]
                featurePositionInTile = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_POSITION]
                fileIdAndPositionInTile = str(featureFileId) + '_' + str(featurePositionInTile)
                featureClassNew = feature[qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW]
                featureChanges = False
                if fileIdAndPositionInTile in updatedPointsFileIdAndPositionInTile:
                    index = updatedPointsFileIdAndPositionInTile.index(fileIdAndPositionInTile)
                    updatingPointClassNew = updatedPointsClassNew[index]
                    if featureClassNew != updatingPointClassNew:
                        feature.setAttribute(qLidarDefinitions.CONST_TILE_FIELD_NAME_CLASS_NEW, updatingPointClassNew)
                        featureChanges = True
                if featureChanges:
                    if not existsChanges:
                        existsChanges = True
                    if not layerInEdition:
                        layer.startEditing()
                        layerInEdition = True
                    layer.updateFeature(feature)
            progressFeatures.close()
            if existsChanges:
                layer.commitChanges()
                layer.triggerRepaint()
            layer.removeSelection()
        progress.close()

    def view3DSelectedPoints(self):
        loadFullTiles = False
        loadFullTiles = self.fullTiles3dCheckBox.isChecked()
        wktGeom = None
        if self.toolRectangle3D:
            wktGeom = self.toolRectangle3D.getWktGeomeetry()
            self.toolRectangle3D.endSelection.disconnect(self.view3DSelectedPoints)
            self.toolRectangle3D.rubberBand.hide()
            self.toolRectangle3D = None
            self.iface.mapCanvas().unsetMapTool(self.toolRectangle3D)
            self.toolButton_SelectByRectangle_3D.setChecked(False)
        elif self.toolPolygon3D:
            wktGeom = self.toolPolygon3D.getWktGeomeetry()
            self.toolPolygon3D.endSelection.disconnect(self.view3DSelectedPoints)
            self.toolPolygon3D.rubberBand.hide()
            self.toolPolygon3D.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
            self.toolPolygon3D.reset()
            self.toolPolygon3D = None
            self.iface.mapCanvas().unsetMapTool(self.toolPolygon3D)
            self.toolButton_SelectByPolygon_3D.setChecked(False)
        elif self.toolFreehand3D:
            wktGeom = self.toolFreehand3D.getWktGeomeetry()
            self.toolFreehand3D.endSelection.disconnect(self.view3DSelectedPoints)
            self.toolFreehand3D.rubberBand.hide()
            self.toolFreehand3D.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
            self.toolFreehand3D.reset()
            self.toolFreehand3D = None
            self.iface.mapCanvas().unsetMapTool(self.toolFreehand3D)
            self.toolButton_SelectByFreehand_3D.setChecked(False)
        if wktGeom:
            projectCrs = QgsProject.instance().crs()
            projectCrsEpsgCode = -1
            projectCrsProj4 = ""
            projectCrsAuthId = projectCrs.authid()
            if "EPSG" in projectCrsAuthId:
                projectCrsEpsgCode = int(projectCrsAuthId.replace("EPSG:", ""))
            projectCrsProj4 = projectCrs.toProj4()
            ret = self.iPyProject.pctGetTilesFromWktGeometry(self.projectPath,
                                                             wktGeom,
                                                             projectCrsEpsgCode,
                                                             projectCrsProj4)
            if ret[0] == "False":
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Error:\n" + ret[1])
                msgBox.exec_()
                return
            numberOfTiles = ret[1]
            if numberOfTiles == 0:
                text = "There are no new tiles to load"
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText(text)
                msgBox.exec_()
                return
            if len(self.loadedTiles) > 0:
                text = "There are " + str(len(self.loadedTiles))
                text += "\ntiles loaded in Map Canvas"
                text += "\nand the process could be slow."
                text += "\n\nDo you wish unload from map canvas these tiles and continue?"
                reply = QMessageBox.question(self.iface.mainWindow(), qLidarDefinitions.CONST_PROGRAM_TITLE,
                                             text, QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.unloadAllTiles()
                else:
                    return
            # tilesNames =ret[2]
            if qLidarDefinitions.CONST_MAX_POINT_TILES > 0:
                if numberOfTiles > qLidarDefinitions.CONST_MAX_POINT_TILES:
                    text = "The number of tiles to load is limited to "
                    text += str(qLidarDefinitions.CONST_MAX_POINT_TILES)
                    text += "\nto avoid performance problems"
                    msgBox = QMessageBox(self)
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setWindowTitle(self.windowTitle)
                    msgBox.setText(text)
                    msgBox.exec_()
                    # text = str(numberOfTiles) + " tiles will be loaded"
                    # text += "\n\nContinue?"
                    # reply = QMessageBox.question(self.iface.mainWindow(), qLidarDefinitions.CONST_PROGRAM_TITLE,
                    #                              text, QMessageBox.Yes, QMessageBox.No)
                    # if reply == QMessageBox.No:
                    #     return
                    return
            self.view3D(wktGeom,loadFullTiles)
        return

    def updateMinScales(self):
        self.minScaleComboBox.currentIndexChanged.disconnect(self.selectMinScale)
        self.minScaleComboBox.clear()
        scales = self.scales
        if not self.minimumScale in scales:
            bisect.insort(scales, self.minimumScale)
        pos = 0
        cont = 0
        for scale in self.scales:
            strScale = "Min.Scale: 1/" + str(scale)
            self.minScaleComboBox.addItem(strScale)
            if scale==self.minimumScale:
                pos = cont
            cont = cont + 1
        self.minScaleComboBox.setCurrentIndex(pos)
        self.minScaleComboBox.currentIndexChanged.connect(self.selectMinScale)
        return

    def view3dMapCanvas(self):
        loadFullTiles = True
        mapCanvasExtend = self.iface.mapCanvas().extent()
        maxFc = mapCanvasExtend.xMaximum()
        maxSc = mapCanvasExtend.yMaximum()
        minFc = mapCanvasExtend.xMinimum()
        minSc = mapCanvasExtend.yMinimum()
        mapCanvasWkt = 'POLYGON((' + str(minFc)+ ' '+str(maxSc) + ',' \
                        + str(maxFc) + ' ' + str(maxSc) + ',' \
                        + str(maxFc) + ' ' + str(minSc) + ',' \
                        + str(minFc) + ' ' + str(minSc) + ',' \
                        + str(minFc) + ' ' + str(maxSc) + '))'
        projectCrs = QgsProject.instance().crs()
        projectCrsEpsgCode = -1
        projectCrsProj4 = ""
        projectCrsAuthId = projectCrs.authid()
        if "EPSG" in projectCrsAuthId:
            projectCrsEpsgCode = int(projectCrsAuthId.replace("EPSG:",""))
        projectCrsProj4 = projectCrs.toProj4()
        ret = self.iPyProject.pctGetTilesFromWktGeometry(self.projectPath,
                                                         mapCanvasWkt,
                                                         projectCrsEpsgCode,
                                                         projectCrsProj4)
        if ret[0] == "False":
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Error:\n" + ret[1])
            msgBox.exec_()
            return
        numberOfTiles = ret[1]
        if numberOfTiles == 0:
            text = "There are no new tiles to load"
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText(text)
            msgBox.exec_()
            return
        if len(self.loadedTiles) > 0:
            text = "There are " + str(len(self.loadedTiles))
            text += "\ntiles loaded in Map Canvas"
            text += "\nand the process could be slow."
            text += "\n\nDo you wish unload from map canvas these tiles and continue?"
            reply = QMessageBox.question(self.iface.mainWindow(), qLidarDefinitions.CONST_PROGRAM_TITLE,
                                         text, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.unloadAllTiles()
            else:
                return
        # tilesNames =ret[2]
        if qLidarDefinitions.CONST_MAX_POINT_TILES > 0:
            if numberOfTiles > qLidarDefinitions.CONST_MAX_POINT_TILES:
                text = "The number of tiles to load is limited to "
                text += str(qLidarDefinitions.CONST_MAX_POINT_TILES)
                text += "\nto avoid performance problems"
                msgBox = QMessageBox(self)
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText(text)
                msgBox.exec_()
                # text = str(numberOfTiles) + " tiles will be loaded"
                # text += "\n\nContinue?"
                # reply = QMessageBox.question(self.iface.mainWindow(), qLidarDefinitions.CONST_PROGRAM_TITLE,
                #                              text, QMessageBox.Yes, QMessageBox.No)
                # if reply == QMessageBox.No:
                #     return
                return
        self.view3D(mapCanvasWkt,loadFullTiles)
        return
