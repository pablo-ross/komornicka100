# GPX Route Verification Guide

This document explains how the GPX route verification works in the Komornicka 100 application and how to test and fine-tune it.

## How Route Verification Works

The application verifies if a Strava activity matches a predefined route by comparing GPS points:

1. The system retrieves the activity data from Strava, including GPS coordinates
2. It simplifies both the source route (from a GPX file) and the user's activity route using the Douglas-Peucker algorithm
3. For each point in the user's activity, it calculates the distance to the closest point on the source route
4. It counts how many points are within the maximum deviation threshold (default: 20 meters)
5. The similarity score is calculated as the percentage of points within this threshold
6. If the similarity score exceeds the threshold (default: 80%) and the activity distance is at least the minimum required (default: 100 km), the activity is verified

## Setting Up Test Routes

### Creating GPX Files

1. Create or export GPX files for your test routes:
   - You can create routes using services like [Strava Route Builder](https://www.strava.com/routes/new)
   - Export routes from Strava, Komoot, RideWithGPS, or other services
   - Use GPS tracking devices to record routes

2. Place your GPX files in the `gpx/` directory of the application

### Setting Verification Parameters

Adjust the verification parameters in your `.env` file:

```
# GPX verification settings
ROUTE_SIMILARITY_THRESHOLD=0.8  # 80% similarity required for verification
GPS_MAX_DEVIATION_METERS=20.0   # 20 meters max deviation
MIN_ACTIVITY_DISTANCE_KM=100.0  # 100 kilometers minimum required
```

## Testing Verification

### Manual Testing

1. Create a test script to manually test the verification logic:

```python
# test_verification.py
import asyncio
import gpxpy
from pathlib import Path
from backend.app.services.gpx_comparison import load_gpx_points, simplify_points, verify_activity_against_source

async def test_verification():
    # Load source GPX file
    source_path = Path("gpx/route1.gpx")
    with open(source_path, "r") as f:
        source_content = f.read()
    
    # Load test activity GPX file (this would be from Strava in the real app)
    test_path = Path("test_activities/activity1.gpx")
    with open(test_path, "r") as f:
        test_content = f.read()
    
    # Parse test activity to get points and distance
    test_gpx = gpxpy.parse(test_content)
    activity_points = []
    for track in test_gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                activity_points.append((point.latitude, point.longitude))
    
    # Calculate activity distance
    activity_distance = 0
    for track in test_gpx.tracks:
        for segment in track.segments:
            activity_distance += segment.length_2d()
    
    # Run verification
    result = verify_activity_against_source(
        source_content, activity_points, activity_distance
    )
    
    print(f"Verification result: {result}")
    print(f"Verified: {result['verified']}")
    print(f"Similarity score: {result['similarity_score']:.2%}")
    print(f"Message: {result['message']}")

if __name__ == "__main__":
    asyncio.run(test_verification())
```

2. Run the test script:
```bash
python test_verification.py
```

### Debugging Verification

To debug the verification process:

1. Add detailed logging to your verification code:

```python
def calculate_similarity(source_points, activity_points, max_deviation=20.0):
    """Calculate similarity between source route and activity route"""
    # Create LineString from source points
    source_line = LineString([(p[1], p[0]) for p in source_points])
    
    # Check each activity point against the source line
    deviations = []
    points_within_threshold = 0
    total_points = len(activity_points)
    
    print(f"Total activity points: {total_points}")
    print(f"Maximum deviation threshold: {max_deviation} meters")
    
    # Sample some points for detailed logging
    sample_indices = [int(total_points * i / 10) for i in range(10)]
    
    for i, (lat, lon) in enumerate(activity_points):
        point = Point(lon, lat)
        distance = source_line.distance(point) * 111319.9  # Convert degrees to meters
        deviations.append((lat, lon, distance))
        
        if distance <= max_deviation:
            points_within_threshold += 1
        
        if i in sample_indices:
            print(f"Sample point {i}: ({lat}, {lon}) - Distance: {distance:.2f}m - {'Within' if distance <= max_deviation else 'Outside'} threshold")
    
    similarity_score = points_within_threshold / total_points if total_points else 0
    print(f"Points within threshold: {points_within_threshold}/{total_points} ({similarity_score:.2%})")
    
    return similarity_score, deviations
```

2. Visualize routes for better debugging:
   - Use a tool like [GPX Viewer](https://www.gpxviewer.xyz/) to visualize both routes
   - Create a script to generate a visualization of both routes with deviation markers

### Creating a Testing Tool

For easier testing, create a simple web interface:

1. Add a route in your FastAPI application:

```python
@router.post("/internal/test-verification")
async def test_verification(
    source_gpx_id: str = Form(...),
    activity_file: UploadFile = File(...)
):
    """Test GPX verification with uploaded file"""
    # Load source GPX
    db = get_db()
    source_gpx = db.query(models.SourceGPX).filter(
        models.SourceGPX.id == source_gpx_id
    ).first()
    
    if not source_gpx:
        raise HTTPException(status_code=404, detail="Source GPX not found")
    
    success, content = await load_source_gpx_file(source_gpx.filename)
    if not success:
        raise HTTPException(status_code=500, detail=f"Error loading source GPX: {content}")
    
    # Read uploaded activity file
    activity_content = await activity_file.read()
    
    try:
        # Parse activity GPX
        gpx = gpxpy.parse(activity_content.decode('utf-8'))
        
        # Extract points
        activity_points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    activity_points.append((point.latitude, point.longitude))
        
        # Calculate distance
        activity_distance = 0
        for track in gpx.tracks:
            for segment in track.segments:
                activity_distance += segment.length_2d()
        
        # Verify
        result = verify_activity_against_source(
            content, activity_points, activity_distance
        )
        
        return {
            "source_gpx": {
                "id": source_gpx.id,
                "name": source_gpx.name,
                "distance_km": source_gpx.distance / 1000
            },
            "activity": {
                "filename": activity_file.filename,
                "points_count": len(activity_points),
                "distance_km": activity_distance / 1000
            },
            "verification_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing GPX: {str(e)}")
```

2. Create a simple HTML form to test this endpoint

## Fine-tuning Verification

### Adjusting Similarity Threshold

The similarity threshold determines how strictly the activity must match the source route:

- **Higher threshold** (e.g., 0.9 or 90%): More strict matching, fewer false positives
- **Lower threshold** (e.g., 0.7 or 70%): More forgiving matching, fewer false negatives

Adjust based on your testing results and requirements.

### Adjusting Maximum Deviation

The maximum deviation determines how far points can be from the route:

- **Lower values** (e.g., 10 meters): Require more precise GPS tracking
- **Higher values** (e.g., 30 meters): More forgiving of GPS inaccuracies

Consider factors like:
- GPS accuracy of typical devices used by participants
- Types of terrain (urban areas with tall buildings may have worse GPS accuracy)
- Width of roads and trails

### Other Considerations

1. **Route Direction**: The current algorithm doesn't consider the direction of travel. If riding the route in reverse should not be allowed, additional checks are needed.

2. **Start and End Points**: If you need to verify that activities start and end at specific points, add additional verification steps.

3. **Minimum Distance**: Adjust the minimum required distance based on your contest rules.

## Troubleshooting

### Common Issues

1. **False Negatives** (valid activities not being verified):
   - GPS data may be inaccurate in certain areas
   - The deviation threshold may be too strict
   - The similarity threshold may be too high

2. **False Positives** (invalid activities being verified):
   - The deviation threshold may be too generous
   - The similarity threshold may be too low
   - Consider adding additional verification criteria

### Analyzing Failed Verifications

For activities that fail verification:

1. Save the activity data for analysis
2. Visualize both the source route and the activity route
3. Analyze where and why the verification failed
4. Adjust parameters or algorithm as needed

### Gathering Feedback

Collect feedback from participants to improve the verification system:

1. Allow users to report verification issues
2. Review reported issues to identify patterns
3. Adjust verification parameters based on real-world usage