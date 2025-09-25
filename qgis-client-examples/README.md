# QGIS Client Examples

This directory contains example implementations of QGIS clients that connect to QGIS Server.

## Files

### 1. python-client.py
A standalone Python script that demonstrates:
- Connecting to WMS/WFS services
- Retrieving map images
- Querying vector features
- Getting feature information
- Spatial and attribute filtering

**Requirements:**
```bash
pip install requests owslib geopandas matplotlib
```

**Usage:**
```bash
python python-client.py
```

### 2. javascript-client.html
A web-based client using OpenLayers that provides:
- Interactive map interface
- Layer control panel
- Feature information on click
- WFS query capabilities
- Map export functionality

**Usage:**
Simply open the HTML file in a web browser. Make sure QGIS Server is running and accessible.

### 3. qgis-desktop-client.py
A Python script for use within QGIS Desktop that offers:
- GUI dialog for server connection
- Automated layer discovery
- Batch layer loading
- Custom styling and labeling

**Usage:**
1. Open QGIS Desktop
2. Open Python Console (Plugins → Python Console)
3. Load and run the script
4. Use the connection dialog or run example functions

## Configuration

All examples assume QGIS Server is running at `http://localhost/qgis-server`. Update the server URL in each script to match your setup:

- Python client: `server_url = "http://localhost/qgis-server"`
- JavaScript client: `const QGIS_SERVER_URL = 'http://localhost/qgis-server';`
- QGIS Desktop client: Update URL in the dialog or script

## Features Demonstrated

1. **Service Discovery**
   - GetCapabilities requests
   - Layer enumeration
   - Service metadata

2. **Map Rendering**
   - WMS GetMap requests
   - Dynamic styling
   - Transparency support

3. **Vector Data Access**
   - WFS GetFeature requests
   - GeoJSON output
   - Attribute filtering (CQL)
   - Spatial filtering

4. **Interactive Features**
   - GetFeatureInfo queries
   - Click handling
   - Feature selection

5. **Advanced Usage**
   - Authentication
   - Custom projections
   - Print layouts
   - Legend graphics