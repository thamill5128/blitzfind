# Complete Guide: Using QGIS Client with QGIS Server

## Overview

QGIS Server is an open-source implementation of the OGC (Open Geospatial Consortium) standards that allows you to publish QGIS projects as web services. QGIS Desktop acts as the client for designing and testing these services.

## Architecture Overview

```
QGIS Desktop (Client) → QGIS Project (.qgs/.qgz) → QGIS Server → Web Services (WMS/WFS/WCS)
                                                                        ↓
                                                              Other Clients (Web/Desktop)
```

## 1. Setting Up QGIS Server

### Installation on Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install QGIS Server
sudo apt install qgis-server

# Install web server (Apache)
sudo apt install apache2 libapache2-mod-fcgid

# Enable required Apache modules
sudo a2enmod rewrite
sudo a2enmod cgid
sudo a2enmod fcgid
sudo a2enmod headers

# Restart Apache
sudo systemctl restart apache2
```

### Installation on Other Systems

For CentOS/RHEL:
```bash
sudo yum install qgis-server
```

For Windows:
- Download QGIS installer from https://qgis.org
- Select QGIS Server component during installation

## 2. Configuring QGIS Server

### Apache Configuration

Create a new configuration file:
```bash
sudo nano /etc/apache2/sites-available/qgis-server.conf
```

Add the following configuration:
```apache
<VirtualHost *:80>
    ServerName localhost
    
    # QGIS Server configuration
    ScriptAlias /qgis-server /usr/lib/cgi-bin/qgis_mapserv.fcgi
    
    <Directory "/usr/lib/cgi-bin">
        AllowOverride None
        Options +ExecCGI -MultiViews +FollowSymLinks
        Require all granted
    </Directory>
    
    # Set QGIS project file location
    SetEnv QGIS_PROJECT_FILE /var/www/qgis/projects/myproject.qgs
    
    # Optional: Set additional environment variables
    SetEnv QGIS_SERVER_LOG_LEVEL 0
    SetEnv QGIS_SERVER_LOG_FILE /var/log/qgis/qgis-server.log
    
    # Enable CORS (if needed for web clients)
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Methods "GET, POST"
    Header set Access-Control-Allow-Headers "Content-Type"
</VirtualHost>
```

Enable the site:
```bash
sudo a2ensite qgis-server
sudo systemctl reload apache2
```

### Nginx Configuration (Alternative)

If using Nginx:
```nginx
server {
    listen 80;
    server_name localhost;
    
    location /qgis-server {
        gzip off;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME /usr/lib/cgi-bin/qgis_mapserv.fcgi;
        fastcgi_param QGIS_PROJECT_FILE /var/www/qgis/projects/myproject.qgs;
        fastcgi_pass unix:/var/run/qgis-server.sock;
    }
}
```

## 3. Preparing QGIS Projects for Server

### In QGIS Desktop:

1. **Create/Open Project**
   - Design your map with all required layers
   - Configure symbology, labels, and styles

2. **Configure Project Properties**
   - Go to `Project → Properties → QGIS Server`
   - Set service capabilities:
     ```
     - Title: My QGIS Server Project
     - Abstract: Description of your project
     - Keywords: gis, mapping, data
     - Contact information
     ```

3. **Configure WMS Capabilities**
   - Enable layers for WMS
   - Set layer names and titles
   - Configure extent and CRS

4. **Configure WFS Capabilities**
   - Enable vector layers for WFS
   - Set feature limits if needed

5. **Save Project**
   ```
   Project → Save As → /var/www/qgis/projects/myproject.qgs
   ```

## 4. Testing QGIS Server Services

### GetCapabilities Requests

Test WMS:
```bash
curl "http://localhost/qgis-server?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"
```

Test WFS:
```bash
curl "http://localhost/qgis-server?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities"
```

Test WCS:
```bash
curl "http://localhost/qgis-server?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCapabilities"
```

### GetMap Request (WMS)
```bash
curl "http://localhost/qgis-server?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=layer_name&STYLES=&CRS=EPSG:4326&BBOX=-180,-90,180,90&WIDTH=800&HEIGHT=400&FORMAT=image/png" --output map.png
```

## 5. Connecting QGIS Desktop Client to QGIS Server

### Adding WMS/WMTS Connection

1. In QGIS Desktop, go to `Layer → Add Layer → Add WMS/WMTS Layer`
2. Click "New" to create a new connection
3. Fill in the connection details:
   ```
   Name: My QGIS Server
   URL: http://localhost/qgis-server
   ```
4. Click "OK" and then "Connect"
5. Select layers to add to your map

### Adding WFS Connection

1. Go to `Layer → Add Layer → Add WFS Layer`
2. Click "New" and enter:
   ```
   Name: My QGIS Server WFS
   URL: http://localhost/qgis-server
   ```
3. Connect and add vector layers

### Python Script for Client Connection

```python
from qgis.core import *
from qgis.gui import *

# Initialize QGIS
QgsApplication.setPrefixPath("/usr", True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Create a new project
project = QgsProject.instance()

# Add WMS layer
wms_url = "http://localhost/qgis-server"
wms_layers = "layer_name"
wms_format = "image/png"
wms_crs = "EPSG:4326"

uri = f"url={wms_url}&layers={wms_layers}&format={wms_format}&crs={wms_crs}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
wms_layer = QgsRasterLayer(uri, "My WMS Layer", "wms")

if wms_layer.isValid():
    project.addMapLayer(wms_layer)
    print("WMS layer added successfully")
else:
    print("Failed to load WMS layer")

# Add WFS layer
wfs_uri = f"{wms_url}?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAME=layer_name"
wfs_layer = QgsVectorLayer(wfs_uri, "My WFS Layer", "WFS")

if wfs_layer.isValid():
    project.addMapLayer(wfs_layer)
    print("WFS layer added successfully")

# Clean up
qgs.exitQgis()
```

## 6. Web Client Integration

### Using OpenLayers

```html
<!DOCTYPE html>
<html>
<head>
    <title>QGIS Server Web Client</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ol@v7.3.0/ol.css">
    <script src="https://cdn.jsdelivr.net/npm/ol@v7.3.0/dist/ol.js"></script>
    <style>
        #map { width: 100%; height: 500px; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Create WMS layer
        const wmsLayer = new ol.layer.Image({
            source: new ol.source.ImageWMS({
                url: 'http://localhost/qgis-server',
                params: {
                    'LAYERS': 'layer_name',
                    'FORMAT': 'image/png',
                    'VERSION': '1.3.0'
                },
                serverType: 'qgis'
            })
        });

        // Create map
        const map = new ol.Map({
            target: 'map',
            layers: [
                new ol.layer.Tile({
                    source: new ol.source.OSM()
                }),
                wmsLayer
            ],
            view: new ol.View({
                center: ol.proj.fromLonLat([0, 0]),
                zoom: 2
            })
        });

        // Add GetFeatureInfo on click
        map.on('singleclick', function(evt) {
            const viewResolution = map.getView().getResolution();
            const url = wmsLayer.getSource().getFeatureInfoUrl(
                evt.coordinate,
                viewResolution,
                'EPSG:3857',
                {'INFO_FORMAT': 'text/html'}
            );
            if (url) {
                fetch(url)
                    .then(response => response.text())
                    .then(html => {
                        console.log(html);
                        // Display feature info
                    });
            }
        });
    </script>
</body>
</html>
```

### Using Leaflet

```html
<!DOCTYPE html>
<html>
<head>
    <title>QGIS Server Leaflet Client</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map { height: 500px; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Create map
        const map = L.map('map').setView([0, 0], 2);

        // Add base layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        // Add WMS layer from QGIS Server
        const wmsLayer = L.tileLayer.wms('http://localhost/qgis-server', {
            layers: 'layer_name',
            format: 'image/png',
            transparent: true,
            attribution: 'QGIS Server'
        }).addTo(map);

        // Add WFS layer
        fetch('http://localhost/qgis-server?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAME=layer_name&OUTPUTFORMAT=GeoJSON')
            .then(response => response.json())
            .then(data => {
                L.geoJSON(data, {
                    onEachFeature: function(feature, layer) {
                        if (feature.properties) {
                            layer.bindPopup(JSON.stringify(feature.properties));
                        }
                    }
                }).addTo(map);
            });
    </script>
</body>
</html>
```

## 7. Advanced Configuration

### Multiple Projects

To serve multiple projects, use the MAP parameter:
```apache
# Remove the fixed project file
# SetEnv QGIS_PROJECT_FILE /path/to/project.qgs

# Access projects with MAP parameter:
# http://localhost/qgis-server?MAP=/path/to/project1.qgs&SERVICE=WMS&...
# http://localhost/qgis-server?MAP=/path/to/project2.qgs&SERVICE=WMS&...
```

### PostgreSQL Integration

Store projects in PostgreSQL:
```sql
-- Create database for QGIS projects
CREATE DATABASE qgis_projects;

-- In QGIS Desktop:
-- Project → Save to → PostgreSQL
-- Connect to database and save
```

Configure server to use PostgreSQL:
```apache
SetEnv QGIS_PROJECT_FILE postgresql://user:password@localhost/qgis_projects?sslmode=disable&schema=public&project=myproject
```

### Performance Optimization

1. **Enable Caching**
   ```apache
   # Add to Apache config
   SetEnv QGIS_SERVER_CACHE_DIRECTORY /var/cache/qgis/
   SetEnv QGIS_SERVER_CACHE_SIZE 50000000
   ```

2. **Parallel Rendering**
   ```apache
   SetEnv QGIS_SERVER_PARALLEL_RENDERING 1
   SetEnv QGIS_SERVER_MAX_THREADS 4
   ```

3. **Connection Pooling**
   ```apache
   # For PostgreSQL connections
   SetEnv QGIS_SERVER_DB_MAX_CONNECTIONS 20
   ```

## 8. Security Considerations

### Authentication

1. **Basic Authentication**
   ```apache
   <Directory "/usr/lib/cgi-bin">
       AuthType Basic
       AuthName "QGIS Server"
       AuthUserFile /etc/apache2/.htpasswd
       Require valid-user
   </Directory>
   ```

2. **IP Restrictions**
   ```apache
   <Directory "/usr/lib/cgi-bin">
       Require ip 192.168.1.0/24
   </Directory>
   ```

### HTTPS Configuration

```apache
<VirtualHost *:443>
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem
    
    # ... rest of QGIS Server config ...
</VirtualHost>
```

## 9. Monitoring and Logging

### Enable Logging
```apache
SetEnv QGIS_SERVER_LOG_FILE /var/log/qgis/qgis-server.log
SetEnv QGIS_SERVER_LOG_LEVEL 0  # 0=INFO, 1=WARNING, 2=CRITICAL
```

### Monitor Performance
```bash
# Check server status
curl "http://localhost/qgis-server?SERVICE=WMS&REQUEST=GetCapabilities" -w "\nTime: %{time_total}s\n"

# Check logs
tail -f /var/log/qgis/qgis-server.log
```

## 10. Troubleshooting

### Common Issues

1. **Server Not Responding**
   - Check Apache/Nginx logs
   - Verify QGIS Server installation
   - Check file permissions

2. **Project Not Loading**
   - Verify project file path
   - Check layer data sources
   - Ensure server has database access

3. **Performance Issues**
   - Enable caching
   - Optimize project (simplify styles, reduce layers)
   - Use tile caching solutions

### Debug Mode
```apache
SetEnv QGIS_DEBUG 1
SetEnv QGIS_SERVER_LOG_LEVEL 0
```

## Conclusion

QGIS Server provides a powerful way to publish QGIS projects as standard OGC web services. By following this guide, you can:

- Set up QGIS Server on your infrastructure
- Configure and optimize the server
- Connect various clients (QGIS Desktop, web browsers)
- Implement security and monitoring
- Troubleshoot common issues

The combination of QGIS Desktop for authoring and QGIS Server for publishing creates a complete open-source GIS solution for web mapping.