import contextily as cx
import geodatasets
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px

from shapely.geometry import MultiPoint, Point
from shapely.ops import voronoi_diagram

from srai.regionalizers import VoronoiRegionalizer, geocode_to_region_gdf


def generate_flat_voronoi_diagram_regions(
    seeds_gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    points = MultiPoint(seeds_gdf.geometry.values)

    # Generate 2D diagram
    regions = voronoi_diagram(points)

    # Map geometries to GeoDataFrame
    flat_voronoi_regions = gpd.GeoDataFrame(
        geometry=list(regions.geoms),
        crs="EPSG:4326",
    )
    # Apply indexes from the seeds dataframe
    flat_voronoi_regions.index = gpd.pd.Index(
        flat_voronoi_regions.sjoin(seeds_gdf)["index_right"],
        name="region_id",
    )

    # Clip to Earth boundaries
    flat_voronoi_regions.geometry = flat_voronoi_regions.geometry.clip_by_rect(
        xmin=-180, ymin=-90, xmax=180, ymax=90
    )
    return flat_voronoi_regions
    
def calculate_iou(
    flat_regions: gpd.GeoDataFrame, spherical_regions: gpd.GeoDataFrame
) -> float:
    total_intersections_area = 0
    total_unions_area = 0

    # Iterate all regions
    for index in spherical_regions.index:
        # Find matching spherical and flat Voronoi region
        spherical_region_geometry = spherical_regions.loc[index].geometry
        flat_region_geometry = flat_regions.loc[index].geometry

        # Calculate their intersection area
        intersections_area = spherical_region_geometry.intersection(
            flat_region_geometry
        ).area
        # Calculate their union area
        # Alternative code:
        # spherical_region_geometry.union(flat_region_geometry).area
        unions_area = (
            spherical_region_geometry.area
            + flat_region_geometry.area
            - intersections_area
        )

        # Add to the total sums
        total_intersections_area += intersections_area
        total_unions_area += unions_area

    # Divide the intersection area by the union area
    return round(total_intersections_area / total_unions_area, 3)

earth_points_gdf = gpd.GeoDataFrame(
    geometry=[
        Point(-86.2791, 32.3615),   # 1. Montgomery, AL
        Point(-134.4197, 58.3019),  # 2. Juneau, AK
        Point(-112.0740, 33.4484),  # 3. Phoenix, AZ
        Point(-92.2896, 34.7465),   # 4. Little Rock, AR
        Point(-121.4944, 38.5816),  # 5. Sacramento, CA
        Point(-104.9903, 39.7392),  # 6. Denver, CO
        Point(-72.6734, 41.7658),   # 7. Hartford, CT
        Point(-75.5244, 39.1582),   # 8. Dover, DE
        Point(-84.2807, 30.4383),   # 9. Tallahassee, FL
        Point(-84.3880, 33.7490),   # 10. Atlanta, GA
        Point(-157.8583, 21.3069),  # 11. Honolulu, HI
        Point(-116.2023, 43.6150),  # 12. Boise, ID
        Point(-89.6461, 39.7990),   # 13. Springfield, IL
        Point(-86.1581, 39.7684),   # 14. Indianapolis, IN
        Point(-93.6250, 41.5868),   # 15. Des Moines, IA
        Point(-95.6752, 39.0473),   # 16. Topeka, KS
        Point(-84.8733, 38.1973),   # 17. Frankfort, KY
        Point(-91.1871, 30.4515),   # 18. Baton Rouge, LA
        Point(-69.7795, 44.3106),   # 19. Augusta, ME
        Point(-76.4922, 38.9784),   # 20. Annapolis, MD
        Point(-71.0589, 42.3601),   # 21. Boston, MA
        Point(-84.5555, 42.7325),   # 22. Lansing, MI
        Point(-93.0900, 44.9537),   # 23. St. Paul, MN
        Point(-90.1848, 32.2988),   # 24. Jackson, MS
        Point(-92.1735, 38.5767),   # 25. Jefferson City, MO
        Point(-112.0391, 46.5884),  # 26. Helena, MT
        Point(-96.7026, 40.8136),   # 27. Lincoln, NE
        Point(-119.7674, 39.1638),  # 28. Carson City, NV
        Point(-71.5375, 43.2081),   # 29. Concord, NH
        Point(-74.7597, 40.2206),   # 30. Trenton, NJ
        Point(-105.9378, 35.6870),  # 31. Santa Fe, NM
        Point(-73.7562, 42.6526),   # 32. Albany, NY
        Point(-78.6382, 35.7796),   # 33. Raleigh, NC
        Point(-100.7837, 46.8083),  # 34. Bismarck, ND
        Point(-82.9988, 39.9612),   # 35. Columbus, OH
        Point(-97.5164, 35.4676),   # 36. Oklahoma City, OK
        Point(-123.0351, 44.9429),  # 37. Salem, OR
        Point(-76.8867, 40.2732),   # 38. Harrisburg, PA
        Point(-71.4128, 41.8240),   # 39. Providence, RI
        Point(-81.0348, 34.0007),   # 40. Columbia, SC
        Point(-100.3510, 44.3683),  # 41. Pierre, SD
        Point(-86.7816, 36.1627),   # 42. Nashville, TN
        Point(-97.7431, 30.2672),   # 43. Austin, TX
        Point(-111.8910, 40.7608),  # 44. Salt Lake City, UT
        Point(-72.5754, 44.2601),   # 45. Montpelier, VT
        Point(-77.4360, 37.5407),   # 46. Richmond, VA
        Point(-122.9007, 47.0379),  # 47. Olympia, WA
        Point(-81.6326, 38.3498),   # 48. Charleston, WV
        Point(-89.4012, 43.0731),   # 49. Madison, WI
        Point(-104.8202, 41.1400),  # 50. Cheyenne, WY
    ],
    index=[i for i in range(1, 51)],
    crs="epsg:4326"
)

# First example: 6 points on the earth. Get the flat voronoi, get the spherical voronoi, and compare their shapes
earth_poles_flat_voronoi_regions = generate_flat_voronoi_diagram_regions(
    earth_points_gdf
)

earth_points_spherical_voronoi_regions = VoronoiRegionalizer(
    seeds=earth_points_gdf
).transform()

calculate_iou(
    earth_poles_flat_voronoi_regions, earth_points_spherical_voronoi_regions
)

counties = gpd.read_file("https://raw.githubusercontent.com/holtzy/The-Python-Graph-Gallery/master/static/data/US-counties.geojson")

counties = counties.to_crs(epsg=4326)
fig, axes = plt.subplots(1, 2, figsize=(28, 14), dpi=200)

counties.plot(ax=axes[0], facecolor="none", edgecolor="black", linewidth=0.5,)
counties.plot(ax=axes[1], facecolor="none", edgecolor="black", linewidth=0.5,)


earth_poles_flat_voronoi_regions.plot(ax=axes[0], edgecolor="black", alpha=0.5, color="blue")
earth_points_gdf.plot(ax=axes[0], color="red", markersize=50)
axes[0].set_xlim(-135,-60)
axes[0].set_ylim(20,55)
cx.add_basemap(axes[0], crs=earth_poles_flat_voronoi_regions.crs, source=cx.providers.OpenStreetMap.Mapnik)
axes[0].set_title("Flat Voronoi Regions")

earth_points_spherical_voronoi_regions.plot(ax=axes[1], edgecolor="black", alpha=0.5, color="green")
earth_points_gdf.plot(ax=axes[1], color="red", markersize=50)
axes[1].set_xlim(-135,-60)
axes[1].set_ylim(20,55)
cx.add_basemap(axes[1], crs=earth_points_spherical_voronoi_regions.crs, source=cx.providers.OpenStreetMap.Mapnik)
axes[1].set_title("Spherical Voronoi Regions")

plt.tight_layout()
plt.savefig("voronoi_comparison.png", dpi=150)
print("Saved visualization to voronoi_comparison.png")

# Second example, AED data
#aed_world_gdf = gpd.read_file(
#    "https://raw.githubusercontent.com/RaczeQ/medium-articles/main/articles/spherical-geovoronoi/aed_world.geojson"
#)
#
#aed_flat_voronoi_regions = generate_flat_voronoi_diagram_regions(aed_world_gdf)
#
#aed_spherical_voronoi_regions = VoronoiRegionalizer(
#    seeds=aed_world_gdf, max_meters_between_points=1_000
#).transform()
#
#calculate_iou(aed_flat_voronoi_regions, aed_spherical_voronoi_regions)

# Third example, London
#greater_london_area = geocode_to_region_gdf("Greater London")
#aeds_in_london = aed_world_gdf.sjoin(greater_london_area)
#
#calculate_iou(
#    aed_flat_voronoi_regions.loc[aeds_in_london.index],
#    aed_spherical_voronoi_regions.loc[aeds_in_london.index],
#)
