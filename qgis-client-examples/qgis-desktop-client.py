#!/usr/bin/env python3
"""
QGIS Desktop Client Script
This script can be run within QGIS Desktop Python Console to connect to QGIS Server
"""

from qgis.core import *
from qgis.gui import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class QGISServerConnector:
    """Helper class to connect QGIS Desktop to QGIS Server"""
    
    def __init__(self, server_url, project=None):
        self.server_url = server_url
        self.project = project or QgsProject.instance()
        self.layers_added = []
    
    def add_wms_layer(self, layer_name, layer_title=None, crs='EPSG:4326', styles=''):
        """Add a WMS layer from QGIS Server"""
        
        # Build WMS URI
        uri = QgsDataSourceUri()
        uri.setParam('url', self.server_url)
        uri.setParam('layers', layer_name)
        uri.setParam('styles', styles)
        uri.setParam('crs', crs)
        uri.setParam('format', 'image/png')
        uri.setParam('version', '1.3.0')
        
        # Create WMS layer
        layer_title = layer_title or layer_name
        wms_layer = QgsRasterLayer(uri.uri(False), layer_title, 'wms')
        
        if wms_layer.isValid():
            self.project.addMapLayer(wms_layer)
            self.layers_added.append(wms_layer)
            print(f"Successfully added WMS layer: {layer_title}")
            return wms_layer
        else:
            print(f"Failed to add WMS layer: {layer_title}")
            print(f"Error: {wms_layer.error().message()}")
            return None
    
    def add_wfs_layer(self, layer_name, layer_title=None, crs='EPSG:4326', 
                      filter_expression=None, max_features=None):
        """Add a WFS layer from QGIS Server"""
        
        # Build WFS URI
        uri = QgsDataSourceUri()
        uri.setParam('url', self.server_url)
        uri.setParam('typename', layer_name)
        uri.setParam('version', '2.0.0')
        uri.setParam('srsname', crs)
        
        if filter_expression:
            uri.setParam('filter', filter_expression)
        
        if max_features:
            uri.setParam('maxNumFeatures', str(max_features))
        
        # Create WFS layer
        layer_title = layer_title or layer_name
        wfs_layer = QgsVectorLayer(uri.uri(False), layer_title, 'WFS')
        
        if wfs_layer.isValid():
            self.project.addMapLayer(wfs_layer)
            self.layers_added.append(wfs_layer)
            print(f"Successfully added WFS layer: {layer_title}")
            print(f"Feature count: {wfs_layer.featureCount()}")
            return wfs_layer
        else:
            print(f"Failed to add WFS layer: {layer_title}")
            return None
    
    def add_wcs_layer(self, coverage_name, layer_title=None, crs='EPSG:4326'):
        """Add a WCS layer from QGIS Server"""
        
        # Build WCS URI
        uri = f"url={self.server_url}&identifier={coverage_name}&crs={crs}"
        
        # Create WCS layer
        layer_title = layer_title or coverage_name
        wcs_layer = QgsRasterLayer(uri, layer_title, 'wcs')
        
        if wcs_layer.isValid():
            self.project.addMapLayer(wcs_layer)
            self.layers_added.append(wcs_layer)
            print(f"Successfully added WCS layer: {layer_title}")
            return wcs_layer
        else:
            print(f"Failed to add WCS layer: {layer_title}")
            return None
    
    def get_capabilities(self, service='WMS'):
        """Get capabilities from QGIS Server"""
        
        from urllib.parse import urlencode
        import urllib.request
        import xml.etree.ElementTree as ET
        
        params = {
            'SERVICE': service,
            'VERSION': '1.3.0' if service == 'WMS' else '2.0.0',
            'REQUEST': 'GetCapabilities'
        }
        
        url = f"{self.server_url}?{urlencode(params)}"
        
        try:
            response = urllib.request.urlopen(url)
            xml_content = response.read().decode('utf-8')
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Extract layer information
            layers = []
            if service == 'WMS':
                for layer in root.findall('.//{http://www.opengis.net/wms}Layer'):
                    name = layer.find('{http://www.opengis.net/wms}Name')
                    title = layer.find('{http://www.opengis.net/wms}Title')
                    if name is not None and name.text:
                        layers.append({
                            'name': name.text,
                            'title': title.text if title is not None else name.text
                        })
            elif service == 'WFS':
                for feature in root.findall('.//{http://www.opengis.net/wfs/2.0}FeatureType'):
                    name = feature.find('{http://www.opengis.net/wfs/2.0}Name')
                    title = feature.find('{http://www.opengis.net/wfs/2.0}Title')
                    if name is not None:
                        layers.append({
                            'name': name.text,
                            'title': title.text if title is not None else name.text
                        })
            
            return layers
            
        except Exception as e:
            print(f"Error getting capabilities: {e}")
            return []
    
    def zoom_to_layers(self):
        """Zoom to the extent of all added layers"""
        if self.layers_added:
            extent = QgsRectangle()
            extent.setMinimal()
            
            for layer in self.layers_added:
                layer_extent = layer.extent()
                if not layer_extent.isEmpty():
                    extent.combineExtentWith(layer_extent)
            
            if not extent.isEmpty():
                canvas = iface.mapCanvas()
                canvas.setExtent(extent)
                canvas.refresh()

def create_server_connection_dialog():
    """Create a dialog for connecting to QGIS Server"""
    
    class ServerConnectionDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Connect to QGIS Server")
            self.setModal(True)
            self.resize(600, 400)
            
            # Main layout
            layout = QVBoxLayout()
            
            # Server URL input
            url_layout = QHBoxLayout()
            url_layout.addWidget(QLabel("Server URL:"))
            self.url_input = QLineEdit("http://localhost/qgis-server")
            url_layout.addWidget(self.url_input)
            self.connect_btn = QPushButton("Get Layers")
            self.connect_btn.clicked.connect(self.get_layers)
            url_layout.addWidget(self.connect_btn)
            layout.addLayout(url_layout)
            
            # Tab widget for WMS/WFS
            self.tab_widget = QTabWidget()
            
            # WMS tab
            self.wms_list = QListWidget()
            self.wms_list.setSelectionMode(QAbstractItemView.MultiSelection)
            self.tab_widget.addTab(self.wms_list, "WMS Layers")
            
            # WFS tab
            self.wfs_list = QListWidget()
            self.wfs_list.setSelectionMode(QAbstractItemView.MultiSelection)
            self.tab_widget.addTab(self.wfs_list, "WFS Layers")
            
            layout.addWidget(self.tab_widget)
            
            # Buttons
            button_layout = QHBoxLayout()
            self.add_btn = QPushButton("Add Selected Layers")
            self.add_btn.clicked.connect(self.add_layers)
            button_layout.addWidget(self.add_btn)
            
            self.close_btn = QPushButton("Close")
            self.close_btn.clicked.connect(self.close)
            button_layout.addWidget(self.close_btn)
            
            layout.addLayout(button_layout)
            self.setLayout(layout)
            
            self.connector = None
        
        def get_layers(self):
            """Get available layers from server"""
            server_url = self.url_input.text()
            self.connector = QGISServerConnector(server_url)
            
            # Clear lists
            self.wms_list.clear()
            self.wfs_list.clear()
            
            # Get WMS layers
            wms_layers = self.connector.get_capabilities('WMS')
            for layer in wms_layers:
                item = QListWidgetItem(f"{layer['title']} ({layer['name']})")
                item.setData(Qt.UserRole, layer)
                self.wms_list.addItem(item)
            
            # Get WFS layers
            wfs_layers = self.connector.get_capabilities('WFS')
            for layer in wfs_layers:
                item = QListWidgetItem(f"{layer['title']} ({layer['name']})")
                item.setData(Qt.UserRole, layer)
                self.wfs_list.addItem(item)
            
            QMessageBox.information(self, "Success", 
                                  f"Found {len(wms_layers)} WMS and {len(wfs_layers)} WFS layers")
        
        def add_layers(self):
            """Add selected layers to project"""
            if not self.connector:
                QMessageBox.warning(self, "Error", "Please connect to server first")
                return
            
            # Add selected WMS layers
            for item in self.wms_list.selectedItems():
                layer_info = item.data(Qt.UserRole)
                self.connector.add_wms_layer(layer_info['name'], layer_info['title'])
            
            # Add selected WFS layers
            for item in self.wfs_list.selectedItems():
                layer_info = item.data(Qt.UserRole)
                self.connector.add_wfs_layer(layer_info['name'], layer_info['title'])
            
            # Zoom to layers
            self.connector.zoom_to_layers()
            
            QMessageBox.information(self, "Success", 
                                  f"Added {len(self.connector.layers_added)} layers")
    
    dialog = ServerConnectionDialog(iface.mainWindow())
    dialog.exec_()

# Example usage functions
def example_basic_connection():
    """Basic example of connecting to QGIS Server"""
    
    # Server URL
    server_url = "http://localhost/qgis-server"
    
    # Create connector
    connector = QGISServerConnector(server_url)
    
    # Add WMS layer
    connector.add_wms_layer('countries', 'Countries Layer')
    
    # Add WFS layer with filter
    connector.add_wfs_layer('cities', 'Large Cities', 
                           filter_expression='population > 1000000')
    
    # Zoom to layers
    connector.zoom_to_layers()

def example_advanced_usage():
    """Advanced example with custom styling and processing"""
    
    server_url = "http://localhost/qgis-server"
    connector = QGISServerConnector(server_url)
    
    # Add WFS layer
    cities_layer = connector.add_wfs_layer('cities', 'Cities')
    
    if cities_layer:
        # Apply graduated symbology based on population
        field_name = 'population'
        
        # Create graduated renderer
        ranges = []
        symbol1 = QgsSymbol.defaultSymbol(cities_layer.geometryType())
        symbol1.setColor(QColor(255, 255, 178))
        range1 = QgsRendererRange(0, 100000, symbol1, '< 100k')
        ranges.append(range1)
        
        symbol2 = QgsSymbol.defaultSymbol(cities_layer.geometryType())
        symbol2.setColor(QColor(254, 204, 92))
        range2 = QgsRendererRange(100000, 1000000, symbol2, '100k - 1M')
        ranges.append(range2)
        
        symbol3 = QgsSymbol.defaultSymbol(cities_layer.geometryType())
        symbol3.setColor(QColor(253, 141, 60))
        range3 = QgsRendererRange(1000000, 10000000, symbol3, '> 1M')
        ranges.append(range3)
        
        renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
        cities_layer.setRenderer(renderer)
        cities_layer.triggerRepaint()
        
        # Add labels
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = 'name'
        label_settings.enabled = True
        
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        cities_layer.setLabeling(labeling)
        cities_layer.setLabelsEnabled(True)
        cities_layer.triggerRepaint()

# Run the examples
if __name__ == '__console__':
    # This code runs in QGIS Python Console
    
    # Show connection dialog
    create_server_connection_dialog()
    
    # Or use direct connection
    # example_basic_connection()
    # example_advanced_usage()