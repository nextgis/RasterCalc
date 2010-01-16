# -*- coding: utf-8 -*-

#******************************************************************************
#
# RasterCalc
# ---------------------------------------------------------
# Raster manipulation plugin.
# 
# Based on rewritten rasterlang plugin (C) 2008 by Barry Rowlingson
# and modified example SimpleCalc from pyparsing module
#
# Copyright (C) 2009 GIS-Lab (http://gis-lab.info) and
# Alexander Bruy (alexander.bruy@gmail.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/copyleft/gpl.html>. You can also obtain it by writing
# to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.
#
#******************************************************************************

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import os.path

from rastercalcdialogbase import Ui_RasterCalcDialog

import rastercalcengine
import rastercalcutils as rasterUtils

class RasterCalcDialog( QDialog, Ui_RasterCalcDialog ):
  def __init__( self ):
    QDialog.__init__( self )
    self.setupUi( self )
    
    # simple operations
    QObject.connect( self.btnPower, SIGNAL( "clicked()" ), self.insertSimpleOp )
    QObject.connect( self.btnBand, SIGNAL( "clicked()" ), self.insertSimpleOp )

    # buttons for arifmethics operations
    QObject.connect( self.btnMul, SIGNAL( "clicked()" ), self.insertArifmOp )
    QObject.connect( self.btnDiv, SIGNAL( "clicked()" ), self.insertArifmOp )
    QObject.connect( self.btnSub, SIGNAL( "clicked()" ), self.insertArifmOp )
    QObject.connect( self.btnAdd, SIGNAL( "clicked()" ), self.insertArifmOp )

    # buttons for parentheses
    QObject.connect( self.btnRParen, SIGNAL( "clicked()" ), self.insertParen )
    QObject.connect( self.btnLParen, SIGNAL( "clicked()" ), self.insertParen )

    # presets
    QObject.connect( self.cmbPresets, SIGNAL( "activated( QString )" ), self.insertPreset )

    QObject.connect( self.btnBrowse, SIGNAL( "clicked()" ), self.selectOutputFile )

    # insert layer label when doubleclicked on tree
    QObject.connect( self.rasterTree, SIGNAL( "itemDoubleClicked( QTreeWidgetItem *, int )" ), self.insertRasterLabel )
    QObject.connect( self.rasterTree, SIGNAL( "itemClicked( QTreeWidgetItem *, int )" ), self.fillBandList )
    QObject.connect( self.bandList, SIGNAL( "itemDoubleClicked( QListWidgetItem * )" ), self.putRasterLabel )
    QObject.connect( self.bandList, SIGNAL( "itemClicked( QListWidgetItem * )" ), self.getBandNumber )

    # check exression for validity
    QObject.connect( self.commandTextEdit, SIGNAL( "textChanged()" ), self.checkExpression )

    QObject.connect( self.btnClearCommand, SIGNAL( "clicked()" ), self.clearExpression )

    # disable Ok button
    self.buttonOk = self.buttonBox.button( QDialogButtonBox.Ok )
    self.buttonOk.setText( self.tr( "Calculate" ) )
    self.buttonOk.setEnabled( False )

    self.bandNum = "1"
    
    self.manageGui()

  def manageGui( self ):
    self.mapLayers = filter( lambda l: l.type() == l.RasterLayer, QgsMapLayerRegistry.instance().mapLayers().values() )
    # get names of all raster layers
    self.layerNames = [ str( z.name() ) for z in self.mapLayers ]
    # generate unique aliases for each layer
    self.layerLabels = rasterUtils.uniqueLabels( self.layerNames )

    self.layerInfo = dict( zip( self.layerLabels, self.mapLayers ) )

    rasterUtils.setRasters( dict( [ ( k, None ) for k in self.layerLabels ] ) )

    self.groups = rasterUtils.GroupedLayers()
    for layer, label in zip( self.mapLayers, self.layerLabels ):
      self.groups.addLayer( layer, label )
    # populate tree widget with layers
    self.setTree( self.groups )

    # set default pixel format to Float32
    self.cmbPixelFormat.setCurrentIndex( self.cmbPixelFormat.findText( "Float32" ) )

  def setTree( self, layersGroups ):
    self.rasterTree.clear()
    for group in layersGroups.groups:
      groupItem = QTreeWidgetItem( self.rasterTree )
      groupItem.setText( 0, group.info )
      groupItem.setFirstColumnSpanned( True )
      groupItem.setExpanded( True )
      # populate group with members
      for layer, label in zip( group.layers, group.labels ):
        memberItem = QTreeWidgetItem( groupItem )
        memberItem.setText( 0, str( layer.name() ) )
        memberItem.setText( 1, label )
        memberItem.setText( 2, str( layer.bandCount() ) )

  def insertRasterLabel( self, item, col ):
    textCursor = self.commandTextEdit.textCursor()
    layer = item.text( 1 ) + "@" + self.bandNum
    textCursor.insertText( layer )

  def fillBandList( self, item, col ):
    self.bandList.clear()
    if item.text( 0 ).startsWith( "Group" ):
      self.bandList.clear()
      return
    bandNum = int( item.text( 2 ) )
    if bandNum == 1:
      self.bandList.addItem( "1" )
    else:
      for i in range( bandNum ):
        self.bandList.addItem( str( i + 1 ) )
    self.rasterName = item.text( 1 )
    self.bandNum = "1"

  def putRasterLabel( self, item ):
    textCursor = self.commandTextEdit.textCursor()
    layer = self.rasterName + "@" + self.bandNum
    textCursor.insertText( layer )

  def getBandNumber( self, item ):
    self.bandNum = item.text()

  def clearExpression( self ):
    self.commandTextEdit.clear()

  def insertPreset( self, preset ):
    self.commandTextEdit.clear()
    if preset == "NDVI (TM/ETM+)":
      self.commandTextEdit.insertPlainText( "( [raster]@3 + [raster]@4 ) / ( [raster]@3 - [raster]@4 )" )
    elif preset == "Difference":
      self.commandTextEdit.insertPlainText( "[raster]@1 - [raster]@2" )

  def insertSimpleOp( self ):
    btn = self.sender()
    if btn.metaObject().className() == "QPushButton":
      btnText = btn.text()
      self.commandTextEdit.insertPlainText( btnText )

  def insertArifmOp( self ):
    btn = self.sender()
    if btn.metaObject().className() == "QPushButton":
      opText = " " + btn.text() + " "
      self.commandTextEdit.insertPlainText( opText )

  def insertParen( self ):
    btn = self.sender()
    if btn.metaObject().className() == "QPushButton":
      paren = btn.text()
      if paren == "(":
        paren += " "
      else:
        paren =  " " + paren
      self.commandTextEdit.insertPlainText( paren )

  def showHelp( self ):
    pass

  def accept( self ):
    #TODO: добавлять в выходной растр информацию о проекции
    if self.leFileName.text().isEmpty():
      QMessageBox.warning( self, self.tr( "Error" ), self.tr( "Please specify output raster" ) )
      return

    rastercalcengine.exprStack = []
    usedRasters = rasterUtils.rasterList
    setRasters = dict()
    for r in usedRasters:
      setRasters[ r ] = rasterUtils.layerAsArray( self.layerInfo[ r ] )
    rasterUtils.setRasters( setRasters )

    expression = rastercalcengine.pattern.parseString( str( self.commandTextEdit.toPlainText() ) )

    self.lblStatusMessage.setText( self.tr( "Running..." ) )

    result = rastercalcengine.evaluateStack( rastercalcengine.exprStack )

    # check is the result array
    if not rasterUtils.isArray( result ):
      QMessageBox.warning( self, self.tr( "Error" ), self.tr( "Result is not an array." ) )
      lblStatusMessage.setText( self.tr( "Failed" ) )
      return

    # time to write results on disk as raster file
    # use the extent of the first layer referenced
    extent = rasterUtils.Extent( self.layerInfo[ list( usedRasters )[ 0 ] ] )

    # make sure result is numpy/Numeric
    ( testFlag, res ) = rasterUtils.checkSameAs( result, setRasters[ list( usedRasters )[ 0 ] ] )
    if not testFlag:
      result = res
    
    #if self.leFileName.text().isEmpty():
    #  QMessageBox.warning( self, self.tr( "Error" ), self.tr( "Please specify output raster" ) )
    #  return

    fileName = os.path.normpath( str( self.leFileName.text() ) )
    pixelFormat = str( self.cmbPixelFormat.currentText() )
    rasterUtils.writeGeoTiff( result, [ extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum() ], pixelFormat, fileName )
    
    # add created layer to the map canvas if neсessary
    if self.loadCheckBox.isChecked():
      newLayer = QgsRasterLayer( fileName, os.path.basename( fileName ) )
      QgsMapLayerRegistry.instance().addMapLayer( newLayer )

    self.lblStatusMessage.setText( self.tr( "Completed" ) )
    
    #self.commandTextEdit.clear()
    #self.buttonOk.setEnabled( False )

  def checkExpression( self ):
    expr = self.commandTextEdit.toPlainText()

    # nothing entered, so exit
    if expr.isEmpty():
      self.lblStatusMessage.setText( "" )
      return

    # check syntax
    rastercalcengine.rasterList = set( [] )
    try:
      rastercalcengine.pattern.parseString( str( expr ) )
    except:
      self.lblStatusMessage.setText( self.tr( "Syntax error" ) )
      self.buttonOk.setEnabled( False )
      return
    
    # check for layers existense
    if len( rastercalcengine.rasterList ) < 1:
      self.lblStatusMessage.setText( self.tr( "Expression must contain at least one layer" ) )
      self.buttonOk.setEnabled( False )
      return
    
    # check for valid labels
    for l in rastercalcengine.rasterList:
      if l not in self.layerLabels:
        self.lblStatusMessage.setText( self.tr( "Unknown raster" ) )
        self.buttonOk.setEnabled( False )
        return

    # check layers compatibility
    groups = [ self.groups.findGroup( self.layerInfo[ l ] ) for l in rastercalcengine.rasterList ]
    if len( set( groups ) ) != 1:
      self.lblStatusMessage.setText( self.tr( "In expression must be layers from one group" ) )
      self.buttonOk.setEnabled( False )
      return

    # all ok
    self.lblStatusMessage.setText( self.tr( "Expression is valid" ) )
    self.buttonOk.setEnabled( True )

  def selectOutputFile( self ):
    fileName = QFileDialog.getSaveFileName( self, self.tr( "Save GeoTiff file" ), ".", "GTiff (*.tif *tiff *.TIF *.TIFF)" )

    if fileName.isEmpty():
      return

    # ensure the user never ommited the extension from the file name
    if not fileName.toLower().endsWith( ".tiff" ):
      if not fileName.toLower().endsWith( ".tif" ):
        fileName += ".tif"

    self.leFileName.setText( fileName )

