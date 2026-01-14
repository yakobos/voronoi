from flask import Flask, render_template, jsonify, request
import json
import os
import geopandas as gpd
from shapely.geometry import Point, box
from srai.regionalizers import VoronoiRegionalizer

app = Flask(__name__)

POINTS_FILE = "points.json"

def load_points():
    if os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_points(points):
    with open(POINTS_FILE, "w") as f:
        json.dump(points, f)

def generate_voronoi_geojson(points):
    if len(points) < 4:
        return None
    
    try:
        geometries = [Point(p["lng"], p["lat"]) for p in points]
        seeds_gdf = gpd.GeoDataFrame(
            geometry=geometries,
            index=list(range(len(points))),
            crs="EPSG:4326",
        )
        
        lngs = [p["lng"] for p in points]
        lats = [p["lat"] for p in points]
        padding = 2.0
        min_lng = max(-180, min(lngs) - padding)
        max_lng = min(180, max(lngs) + padding)
        min_lat = max(-90, min(lats) - padding)
        max_lat = min(90, max(lats) + padding)
        clip_box = box(min_lng, min_lat, max_lng, max_lat)
        
        regionalizer = VoronoiRegionalizer(
            seeds=seeds_gdf,
            max_meters_between_points=50_000
        )
        spherical_regions = regionalizer.transform()
        
        spherical_regions["geometry"] = spherical_regions.geometry.intersection(clip_box)
        spherical_regions = spherical_regions[~spherical_regions.geometry.is_empty]
        
        geojson = json.loads(spherical_regions.to_json())
        
        for feature in geojson["features"]:
            point_idx = feature.get("id")
            if point_idx is not None:
                point_idx = int(point_idx)
                if point_idx < len(points):
                    feature["properties"]["category"] = points[point_idx].get("category", None)
                    feature["properties"]["point_index"] = point_idx
        
        return geojson
    except Exception as e:
        print(f"Voronoi error: {e}")
        return None

@app.route('/')
def index():
    points = load_points()
    return render_template('index.html', points=points)

@app.route('/save_points', methods=['POST'])
def save_points_route():
    points = request.json
    save_points(points)
    return jsonify({"status": "ok"})

@app.route('/get_points')
def get_points():
    return jsonify(load_points())

@app.route('/voronoi')
def voronoi():
    points = load_points()
    geojson = generate_voronoi_geojson(points)
    return jsonify({"geojson": geojson})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
