#!/usr/bin/env python3
"""
QGIS Server Python Client Example
Demonstrates how to connect to QGIS Server services using Python
"""

import requests
import json
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
import matplotlib.pyplot as plt
import geopandas as gpd
from io import BytesIO
import xml.etree.ElementTree as ET

class QGISServerClient:
    """Client for interacting with QGIS Server"""
    
    def __init__(self, server_url):
        self.server_url = server_url
        self.wms = None
        self.wfs = None
    
    def connect_wms(self):
        """Connect to WMS service"""
        try:
            self.wms = WebMapService(f"{self.server_url}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities")
            print(f"Connected to WMS: {self.wms.identification.title}")
            print(f"Available layers: {list(self.wms.contents.keys())}")
            return True
        except Exception as e:
            print(f"Error connecting to WMS: {e}")
            return False
    
    def connect_wfs(self):
        """Connect to WFS service"""
        try:
            self.wfs = WebFeatureService(f"{self.server_url}?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities")
            print(f"Connected to WFS: {self.wfs.identification.title}")
            print(f"Available features: {list(self.wfs.contents.keys())}")
            return True
        except Exception as e:
            print(f"Error connecting to WFS: {e}")
            return False
    
    def get_map_image(self, layers, bbox, width=800, height=600, srs='EPSG:4326', format='image/png'):
        """Get map image from WMS"""
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'LAYERS': layers,
            'STYLES': '',
            'CRS': srs,
            'BBOX': ','.join(map(str, bbox)),
            'WIDTH': width,
            'HEIGHT': height,
            'FORMAT': format
        }
        
        response = requests.get(self.server_url, params=params)
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            print(f"Error getting map: {response.status_code}")
            return None
    
    def get_features(self, typename, output_format='GeoJSON', max_features=100):
        """Get features from WFS"""
        params = {
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': typename,
            'OUTPUTFORMAT': output_format,
            'COUNT': max_features
        }
        
        response = requests.get(self.server_url, params=params)
        if response.status_code == 200:
            if output_format == 'GeoJSON':
                return json.loads(response.text)
            else:
                return response.text
        else:
            print(f"Error getting features: {response.status_code}")
            return None
    
    def get_feature_info(self, layers, x, y, width, height, bbox, srs='EPSG:4326'):
        """Get feature info at specific coordinates"""
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetFeatureInfo',
            'LAYERS': layers,
            'QUERY_LAYERS': layers,
            'INFO_FORMAT': 'application/json',
            'I': x,
            'J': y,
            'WIDTH': width,
            'HEIGHT': height,
            'CRS': srs,
            'BBOX': ','.join(map(str, bbox))
        }
        
        response = requests.get(self.server_url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting feature info: {response.status_code}")
            return None
    
    def get_legend(self, layer, width=20, height=20, format='image/png'):
        """Get legend graphic for a layer"""
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetLegendGraphic',
            'LAYER': layer,
            'FORMAT': format,
            'WIDTH': width,
            'HEIGHT': height
        }
        
        response = requests.get(self.server_url, params=params)
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            print(f"Error getting legend: {response.status_code}")
            return None

def example_usage():
    """Example usage of QGIS Server client"""
    
    # Initialize client
    server_url = "http://localhost/qgis-server"
    client = QGISServerClient(server_url)
    
    # Connect to services
    print("=== Connecting to QGIS Server ===")
    client.connect_wms()
    client.connect_wfs()
    
    # Example 1: Get and display a map
    print("\n=== Getting Map Image ===")
    layers = "countries,cities"  # Replace with your layer names
    bbox = [-180, -90, 180, 90]  # World extent
    
    map_image = client.get_map_image(layers, bbox)
    if map_image:
        # Display the map
        img = plt.imread(map_image)
        plt.figure(figsize=(10, 6))
        plt.imshow(img)
        plt.title("Map from QGIS Server")
        plt.axis('off')
        plt.savefig('/workspace/qgis-client-examples/map_output.png')
        print("Map saved to map_output.png")
    
    # Example 2: Get vector features
    print("\n=== Getting Vector Features ===")
    features = client.get_features('countries', max_features=10)
    if features:
        print(f"Retrieved {len(features['features'])} features")
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(features)
        print("\nFirst 5 features:")
        print(gdf.head())
        
        # Save to file
        gdf.to_file('/workspace/qgis-client-examples/features_output.geojson', driver='GeoJSON')
        print("Features saved to features_output.geojson")
    
    # Example 3: Get feature info at point
    print("\n=== Getting Feature Info ===")
    # Click at center of map
    x, y = 400, 300  # Center of 800x600 image
    info = client.get_feature_info(layers, x, y, 800, 600, bbox)
    if info:
        print("Feature info at click point:")
        print(json.dumps(info, indent=2))
    
    # Example 4: Get legend
    print("\n=== Getting Legend ===")
    legend = client.get_legend('countries')
    if legend:
        legend_img = plt.imread(legend)
        plt.figure(figsize=(4, 6))
        plt.imshow(legend_img)
        plt.title("Layer Legend")
        plt.axis('off')
        plt.savefig('/workspace/qgis-client-examples/legend_output.png')
        print("Legend saved to legend_output.png")

def advanced_example():
    """Advanced example with spatial queries and analysis"""
    
    server_url = "http://localhost/qgis-server"
    
    # Spatial filter example
    print("\n=== Spatial Filter Example ===")
    
    # Get features within a bounding box
    bbox_filter = """
    <Filter xmlns="http://www.opengis.net/ogc">
        <BBOX>
            <PropertyName>geometry</PropertyName>
            <Envelope xmlns="http://www.opengis.net/gml" srsName="EPSG:4326">
                <lowerCorner>-10 40</lowerCorner>
                <upperCorner>30 60</upperCorner>
            </Envelope>
        </BBOX>
    </Filter>
    """
    
    params = {
        'SERVICE': 'WFS',
        'VERSION': '2.0.0',
        'REQUEST': 'GetFeature',
        'TYPENAME': 'countries',
        'OUTPUTFORMAT': 'GeoJSON',
        'FILTER': bbox_filter
    }
    
    response = requests.get(server_url, params=params)
    if response.status_code == 200:
        features = response.json()
        print(f"Found {len(features['features'])} features in bounding box")
    
    # Attribute filter example
    print("\n=== Attribute Filter Example ===")
    
    cql_filter = "population > 1000000"  # Cities with population > 1M
    params = {
        'SERVICE': 'WFS',
        'VERSION': '2.0.0',
        'REQUEST': 'GetFeature',
        'TYPENAME': 'cities',
        'OUTPUTFORMAT': 'GeoJSON',
        'CQL_FILTER': cql_filter
    }
    
    response = requests.get(server_url, params=params)
    if response.status_code == 200:
        features = response.json()
        print(f"Found {len(features['features'])} cities with population > 1M")

if __name__ == "__main__":
    # Create output directory
    import os
    os.makedirs('/workspace/qgis-client-examples', exist_ok=True)
    
    # Run examples
    example_usage()
    advanced_example()