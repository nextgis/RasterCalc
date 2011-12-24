# -*- coding: utf-8 -*-

#******************************************************************************
#
# RasterCalc
# ---------------------------------------------------------
# Raster manipulation plugin.
#
# Based on rewritten rasterlang plugin (C) 2008 by Barry Rowlingson
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

from __init__ import mVersion

import resources

class RasterCalcPlugin( object ):
  def __init__( self, iface ):
    self.iface = iface
    self.iface = iface
    try:
      self.QgisVersion = unicode( QGis.QGIS_VERSION_INT )
    except:
      self.QgisVersion = unicode( QGis.qgisVersion )[ 0 ]

    # For i18n support
    userPluginPath = QFileInfo( QgsApplication.qgisUserDbFilePath() ).path() + "/python/plugins/rastercalc"
    systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/rastercalc"

    overrideLocale = QSettings().value( "locale/overrideFlag", QVariant( False ) ).toBool()
    if not overrideLocale:
      localeFullName = QLocale.system().name()
    else:
      localeFullName = QSettings().value( "locale/userLocale", QVariant( "" ) ).toString()

    if QFileInfo( userPluginPath ).exists():
      translationPath = userPluginPath + "/i18n/rastercalc_" + localeFullName + ".qm"
    else:
      translationPath = systemPluginPath + "/i18n/rastercalc_" + localeFullName + ".qm"

    self.localePath = translationPath
    if QFileInfo( self.localePath ).exists():
      self.translator = QTranslator()
      self.translator.load( self.localePath )
      QCoreApplication.installTranslator( self.translator )


  def initGui( self ):
    if int( self.QgisVersion ) < 1:
      QMessageBox.warning( self.iface.mainWindow(), "RasterCalc",
                           QCoreApplication.translate( "RasterCalc", "Quantum GIS version detected: " ) + unicode( self.QgisVersion ) + ".xx\n" +
                           QCoreApplication.translate( "RasterCalc", "This version of RasterCalc requires at least QGIS version 1.0.0\nPlugin will not be enabled." ) )
      return None

    self.actionRun = QAction( QIcon( ":/rastercalc.png" ), "RasterCalc", self.iface.mainWindow() )
    self.actionRun.setStatusTip( QCoreApplication.translate( "RasterCalc", "Perform raster algebra operations" ) )
    self.actionRun.setWhatsThis( QCoreApplication.translate( "RasterCalc", "Raster algebra" ) )
    self.actionAbout = QAction( QIcon( ":/about.png" ), "About", self.iface.mainWindow() )

    QObject.connect( self.actionRun, SIGNAL( "triggered()" ), self.run )
    QObject.connect( self.actionAbout, SIGNAL( "triggered()" ), self.about )

    if hasattr( self.iface, "addPluginToRasterMenu" ):
      self.iface.addPluginToRasterMenu( QCoreApplication.translate( "RasterCalc", "RasterCalc" ), self.actionRun )
      self.iface.addPluginToRasterMenu( QCoreApplication.translate( "RasterCalc", "RasterCalc" ), self.actionAbout )
      self.iface.addRasterToolBarIcon( self.actionRun )
    else:
      self.iface.addPluginToMenu( QCoreApplication.translate( "RasterCalc", "RasterCalc" ), self.actionRun )
      self.iface.addPluginToMenu( QCoreApplication.translate( "RasterCalc", "RasterCalc" ), self.actionAbout )
      self.iface.addToolBarIcon( self.actionRun )

  def unload( self ):
    if hasattr( self.iface, "addPluginToRasterMenu" ):
      self.iface.removePluginRasterMenu( QCoreApplication.translate( "RasterCalc", "RasterCalc" ), self.actionRun )
      self.iface.removePluginRasterMenu( QCoreApplication.translate( "RasterCalc", "RasterCalc" ), self.actionAbout )
      self.iface.removeRasterToolBarIcon( self.actionRun )
    else:
      self.iface.removePluginMenu( QCoreApplication.translate( "RasterCalc", "RasterCalc" ), self.actionRun )
      self.iface.removePluginMenu( QCoreApplication.translate( "RasterCalc", "RasterCalc" ), self.actionAbout )
      self.iface.removeToolBarIcon( self.actionRun )

  def about( self ):
    dlgAbout = QDialog()
    dlgAbout.setWindowTitle( QApplication.translate( "RasterCalc", "About RasterCalc", "Window title" ) )
    lines = QVBoxLayout( dlgAbout )
    title = QLabel( QApplication.translate( "RasterCalc", "<b>RasterCalc</b>" ) )
    title.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
    lines.addWidget( title )
    version = QLabel( QApplication.translate( "RasterCalc", "Version: %1" ).arg( mVersion ) )
    version.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
    lines.addWidget( version )
    lines.addWidget( QLabel( QApplication.translate( "RasterCalc", "This plugin performs arfmethics operations\non single- and multiband rasters" ) ) )
    lines.addWidget( QLabel( QApplication.translate( "RasterCalc", "<b>Developers:</b>" ) ) )
    lines.addWidget( QLabel( "  Alexander Bruy" ) )
    lines.addWidget( QLabel( "  Maxim Dubinin" ) )
    lines.addWidget( QLabel( "  Barry Rowlingson (portions of code)" ) )
    lines.addWidget( QLabel( QApplication.translate( "RasterCalc", "<b>Homepage:</b>") ) )

    overrideLocale = QSettings().value( "locale/overrideFlag", QVariant( False ) ).toBool()
    if not overrideLocale:
      localeFullName = QLocale.system().name()
    else:
      localeFullName = QSettings().value( "locale/userLocale", QVariant( "" ) ).toString()

    localeShortName = localeFullName[ 0:2 ]
    if localeShortName in [ "ru", "uk" ]:
      link = QLabel( "<a href=\"http://gis-lab.info/qa/rastercalc.html\">http://gis-lab.info/qa/rastercalc.html</a>" )
    else:
      link = QLabel( "<a href=\"http://gis-lab.info/qa/rastercalc-eng.html\">http://gis-lab.info/qa/rastercalc-eng.html</a>" )

    link.setOpenExternalLinks( True )
    lines.addWidget( link )

    btnClose = QPushButton( QApplication.translate( "RasterCalc", "Close" ) )
    lines.addWidget( btnClose )
    QObject.connect( btnClose, SIGNAL( "clicked()" ), dlgAbout, SLOT( "close()" ) )

    dlgAbout.exec_()

  def run( self ):
    # check is all necessary modules are available
    try:
      import pyparsing
    except ImportError, e:
      QMessageBox.information( self.iface.mainWindow(), QCoreApplication.translate( "RasterCalc", "Plugin error" ), QCoreApplication.translate( "RasterCalc", "Couldn't import Python module 'pyparsing'. Without it you won't be able to run RasterCalc." ) )
      return

    try:
      import osgeo.gdal
    except ImportError, e:
      try:
        import gdal
      except:
        pass
      QMessageBox.information( self.iface.mainWindow(), QCoreApplication.translate( "RasterCalc", "Plugin error" ), QCoreApplication.translate( "RasterCalc", "Couldn't import Python module 'osgeo.gdal'. Without it you won't be able to run PasterCalc." ) )
      return

    try:
      import numpy
    except ImportError, e:
      QMessageBox.informtion( self.iface.mainWindow(), QCoreApplication.translate( "RasterCalc", "Plugin error" ), QCoreApplication.translate( "RasterCalc", "Couldn't import Python module 'numpy'. Without it you won't be able to run RasterCalc." ) )
      return

    import rastercalcdialog

    dlg = rastercalcdialog.RasterCalcDialog()
    dlg.exec_()

