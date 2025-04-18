import math
from typing import Dict, List, Tuple

import gpxpy
import gpxpy.gpx
from shapely.geometry import LineString, Point

from ..core.config import settings


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth specified in decimal degrees.
    
    Args:
        lat1: Latitude of point 1
        lon1: Longitude of point 1
        lat2: Latitude of point 2
        lon2: Longitude of point 2
        
    Returns:
        Distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r


def load_gpx_points(gpx_content: str) -> List[Tuple[float, float]]:
    """
    Load points (latitude, longitude) from GPX content
    
    Args:
        gpx_content: GPX file content as string
        
    Returns:
        List of (latitude, longitude) points
    """
    gpx = gpxpy.parse(gpx_content)
    points = []
    
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
    
    return points


def simplify_points(points: List[Tuple[float, float]], tolerance: float = 0.0001) -> List[Tuple[float, float]]:
    """
    Simplify a list of points using Douglas-Peucker algorithm
    
    Args:
        points: List of (latitude, longitude) points
        tolerance: Tolerance for simplification
        
    Returns:
        Simplified list of points
    """
    if len(points) < 3:
        return points
        
    line = LineString([(p[1], p[0]) for p in points])  # (lon, lat) for LineString
    simplified = line.simplify(tolerance)
    
    # Convert back to (lat, lon)
    return [(y, x) for x, y in simplified.coords]


def calculate_similarity(
    source_points: List[Tuple[float, float]],
    activity_points: List[Tuple[float, float]],
    max_deviation: float = 20.0  # Maximum deviation in meters
) -> Tuple[float, List[Tuple[float, float, float]]]:
    """
    Calculate similarity between source route and activity route
    
    Args:
        source_points: List of (lat, lon) points from source route
        activity_points: List of (lat, lon) points from activity
        max_deviation: Maximum allowed deviation in meters
        
    Returns:
        Tuple of (similarity_score, list of deviations)
    """
    # Create LineString from source points
    source_line = LineString([(p[1], p[0]) for p in source_points])  # (lon, lat) for LineString
    
    # Check each activity point against the source line
    deviations = []
    points_within_threshold = 0
    
    for lat, lon in activity_points:
        point = Point(lon, lat)  # (lon, lat) for Point
        distance = source_line.distance(point) * 111319.9  # Convert degrees to meters (approximate)
        deviations.append((lat, lon, distance))
        
        if distance <= max_deviation:
            points_within_threshold += 1
    
    # Calculate similarity score (percentage of points within threshold)
    similarity_score = points_within_threshold / len(activity_points) if activity_points else 0
    
    return similarity_score, deviations


def verify_activity_against_source(
    source_gpx_content: str,
    activity_points: List[Tuple[float, float]],
    activity_distance: float  # Distance in meters
) -> Dict[str, any]:
    """
    Verify if an activity matches a source GPX route
    
    Args:
        source_gpx_content: GPX file content of source route
        activity_points: List of (lat, lon) points from activity
        activity_distance: Distance of activity in meters
        
    Returns:
        Dict with verification results
    """
    # Check minimum distance requirement
    required_distance = settings.MIN_ACTIVITY_DISTANCE_KM * 1000  # Convert to meters
    if activity_distance < required_distance:
        return {
            "verified": False,
            "similarity_score": 0.0,
            "message": f"Activity distance ({activity_distance/1000:.1f}km) is less than required ({settings.MIN_ACTIVITY_DISTANCE_KM}km)"
        }
    
    # Load source route points
    try:
        source_points = load_gpx_points(source_gpx_content)
    except Exception as e:
        return {
            "verified": False,
            "similarity_score": 0.0,
            "message": f"Error loading source GPX: {str(e)}"
        }
    
    # Check if we have enough points
    if len(source_points) < 10 or len(activity_points) < 10:
        return {
            "verified": False,
            "similarity_score": 0.0,
            "message": "Not enough GPS points to perform verification"
        }
    
    # Simplify routes for faster comparison
    source_points = simplify_points(source_points)
    activity_points = simplify_points(activity_points)
    
    # Calculate similarity
    similarity_score, deviations = calculate_similarity(
        source_points,
        activity_points,
        max_deviation=settings.GPS_MAX_DEVIATION_METERS
    )
    
    # Check if similarity meets threshold
    verified = similarity_score >= settings.ROUTE_SIMILARITY_THRESHOLD
    
    return {
        "verified": verified,
        "similarity_score": similarity_score,
        "message": (
            f"Route verified successfully with {similarity_score:.1%} match"
            if verified else
            f"Route similarity ({similarity_score:.1%}) below required threshold ({settings.ROUTE_SIMILARITY_THRESHOLD:.1%})"
        )
    }


def convert_strava_streams_to_points(
    streams: Dict[str, any]
) -> List[Tuple[float, float]]:
    """
    Convert Strava API streams to list of points
    
    Args:
        streams: Strava API streams response
        
    Returns:
        List of (lat, lon) points
    """
    if not streams or "latlng" not in streams:
        return []
    
    latlng_data = streams["latlng"]["data"]
    return [(point[0], point[1]) for point in latlng_data if len(point) == 2]