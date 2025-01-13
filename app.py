from config import Config
from flask import Flask, request, jsonify, abort
from werkzeug.utils import secure_filename
import logging
import gpxpy
from shapely.geometry import LineString
import requests

app = Flask(__name__)



def validate_gpx_file(file):
    """
    Validate the uploaded GPX file format and size.

    Args:
        file: Flask FileStorage object containing the uploaded file.

    Returns:
        FileStorage: The validated file object.

    Raises:
        400: If file is missing or not a GPX file.
        413: If file size exceeds MAX_FILE_SIZE.
    """
    if not file or not file.filename.endswith('.gpx'):
        abort(400, description="Invalid file format. Please upload a GPX file")
    if file.content_length > Config.MAX_FILE_SIZE:
        abort(413, description="File too large")
    return file


def process_gpx_file(gpx_file):
    """
    Parse a GPX file and extract track points.

    Args:
        gpx_file: Flask FileStorage object containing the GPX file.

    Returns:
        list: List of tuples containing (longitude, latitude, elevation) for each track point.

    Raises:
        400: If GPX file format is invalid or parsing fails.
    """
    try:
        gpx = gpxpy.parse(gpx_file.stream)
        points = [(point.longitude, point.latitude, point.elevation)
                 for track in gpx.tracks
                 for segment in track.segments
                 for point in segment.points]
        return points
    except Exception as e:
        logging.error(f"GPX parsing error: {str(e)}")
        abort(400, description="Invalid GPX file format")

def query_overpass_api(bbox, timeout=30):
    """
    Query the Overpass API for ways with surface tags within the specified bounding box.

    Args:
        bbox (str): Bounding box coordinates in format "south,west,north,east".
        timeout (int, optional): API request timeout in seconds. Defaults to 30.

    Returns:
        dict: JSON response from Overpass API containing way geometries and surface information.

    Raises:
        503: If the Overpass API request fails.
    """
    query = f"""
    [out:json][timeout:{timeout}];
    (
      way({bbox})["surface"];
    );
    out geom;
    """
    try:
        response = requests.post(Config.OVERPASS_URL, data=query, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Overpass API error: {str(e)}")
        abort(503, description="External service temporarily unavailable")


def calculate_suitability(surface_data):
    """
    Calculate suitability scores for road and gravel bikes based on surface types.

    Args:
        surface_data (dict): Dictionary mapping surface types to their lengths in kilometers.
                           Example: {"asphalt": 1.5, "gravel": 0.8}

    Returns:
        dict: Suitability scores for road and gravel bikes, each ranging from 0.0 to 1.0.
              Example: {"roadbike": 0.75, "gravelbike": 0.90}

    Note:
        Scores are weighted averages based on the surface lengths and their respective
        suitability factors defined in Config.SURFACE_SUITABILITY.
    """
    total_length = sum(surface_data.values())
    if total_length == 0:
        return {"roadbike": 0.0, "gravelbike": 0.0}

    roadbike_score = 0.0
    gravelbike_score = 0.0

    for surface, length in surface_data.items():
        roadbike_factor, gravelbike_factor = Config.SURFACE_SUITABILITY.get(surface, (0.0, 0.0))
        roadbike_score += (length / total_length) * roadbike_factor
        gravelbike_score += (length / total_length) * gravelbike_factor

    return {"roadbike": round(roadbike_score, 2), "gravelbike": round(gravelbike_score, 2)}

def calculate_elevation_gain(points):
    """
    Calculate the total elevation gain and loss from a series of GPS track points.

    Args:
        points (list): A list of tuples containing (longitude, latitude, elevation) for each track point.
                      Elevation should be in meters.

    Returns:
        dict: A dictionary containing:
            - elevation_up (float): Total elevation gain in meters, rounded to 2 decimal places
            - elevation_down (float): Total elevation loss in meters, rounded to 2 decimal places

    Example:
        >>> points = [(0, 0, 100), (0, 0, 150), (0, 0, 120)]
        >>> calculate_elevation_gain(points)
        {'elevation_up': 50.0, 'elevation_down': 30.0}
    """
    total_up = 0.0
    total_down = 0.0
    
    for i in range(1, len(points)):
        prev_point = points[i-1]
        curr_point = points[i]
        
        # Get elevation difference between consecutive points
        elev_diff = curr_point[2] - prev_point[2]
        if elev_diff > 0:
            total_up += elev_diff
        else:
            total_down += abs(elev_diff)

    return {"elevation_up": round(total_up, 2), "elevation_down": round(total_down, 2)}

def process_road_geometries(roads, buffer):
    road_lengths = {}
    for road in roads.get('elements', []):
        if 'geometry' in road and 'tags' in road:
            geom = LineString([(p['lon'], p['lat']) for p in road['geometry']])
            surface = road['tags'].get('surface', 'unknown')
            intersection = geom.intersection(buffer)
            if not intersection.is_empty:
                length = intersection.length * 111_320  # Convert degrees to meters
                road_lengths[surface] = road_lengths.get(surface, 0) + length
    return road_lengths

@app.route('/analyze_surface', methods=['POST'])
def analyze_surface():
    try:
        gpx_file = validate_gpx_file(request.files.get('gpx_file'))
        points = process_gpx_file(gpx_file)

        if not points:
            abort(400, description="No track points found in GPX file")

        elevation_data = calculate_elevation_gain(points)
        track_line = LineString(points)
        buffer = track_line.buffer(Config.BUFFER_SIZE)

        bbox = f"{buffer.bounds[1]},{buffer.bounds[0]},{buffer.bounds[3]},{buffer.bounds[2]}"
        roads = query_overpass_api(bbox)

        road_lengths = process_road_geometries(roads, buffer)
        road_lengths_km = {surface: round(length / 1_000, 2)
                          for surface, length in road_lengths.items()}
        suitability_scores = calculate_suitability(road_lengths_km)

        return jsonify({
            "surface_lengths_km": road_lengths_km,
            "suitability_scores": suitability_scores,
            "elevation": elevation_data
        })

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        abort(500, description="Internal server error")

if __name__ == '__main__':
    app.run(debug=True)
