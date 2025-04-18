import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gpxpy
import gpxpy.gpx
from fastapi import UploadFile
from sqlalchemy.orm import Session

from .. import models
from ..core.config import settings


async def load_source_gpx_file(filename: str) -> Tuple[bool, str]:
    """
    Load source GPX file content
    
    Args:
        filename: Name of the GPX file in the source GPX directory
        
    Returns:
        Tuple of (success, content or error message)
    """
    try:
        file_path = Path(settings.SOURCE_GPX_PATH) / filename
        
        if not file_path.exists():
            return False, f"File {filename} not found"
        
        with open(file_path, "r") as f:
            content = f.read()
        
        return True, content
    except Exception as e:
        return False, f"Error loading GPX file: {str(e)}"


async def get_source_gpx_info(filename: str) -> Dict[str, any]:
    """
    Get information about a source GPX file
    
    Args:
        filename: Name of the GPX file in the source GPX directory
        
    Returns:
        Dictionary with GPX information
    """
    success, content = await load_source_gpx_file(filename)
    
    if not success:
        return {"error": content}
    
    try:
        gpx = gpxpy.parse(content)
        
        # Calculate total distance
        total_distance = 0
        for track in gpx.tracks:
            for segment in track.segments:
                total_distance += segment.length_2d()
        
        # Get bounds
        min_lat, max_lat, min_lon, max_lon = gpx.get_bounds()
        
        # Count points
        total_points = 0
        for track in gpx.tracks:
            for segment in track.segments:
                total_points += len(segment.points)
        
        return {
            "filename": filename,
            "distance_meters": total_distance,
            "distance_km": total_distance / 1000,
            "bounds": {
                "min_lat": min_lat,
                "max_lat": max_lat,
                "min_lon": min_lon,
                "max_lon": max_lon
            },
            "total_points": total_points,
            "name": gpx.name or "Unnamed Route",
            "description": gpx.description or ""
        }
    except Exception as e:
        return {"error": f"Error parsing GPX file: {str(e)}"}


async def list_available_source_gpx_files() -> List[str]:
    """
    List all available GPX files in the source directory
    
    Returns:
        List of GPX filenames
    """
    try:
        source_dir = Path(settings.SOURCE_GPX_PATH)
        return [f.name for f in source_dir.glob("*.gpx")]
    except Exception as e:
        print(f"Error listing GPX files: {e}")
        return []


async def init_source_gpx_database(db: Session) -> None:
    """
    Initialize source GPX database from files
    
    Args:
        db: Database session
    """
    # List available GPX files
    files = await list_available_source_gpx_files()
    
    for filename in files:
        # Check if already in database
        existing = db.query(models.SourceGPX).filter(models.SourceGPX.filename == filename).first()
        if existing:
            continue
            
        # Get info for new file
        info = await get_source_gpx_info(filename)
        if "error" in info:
            print(f"Error processing {filename}: {info['error']}")
            continue
            
        # Add to database
        new_source = models.SourceGPX(
            name=info.get("name", "Unnamed Route"),
            description=info.get("description", ""),
            filename=filename,
            distance=info.get("distance_meters", 0)
        )
        
        db.add(new_source)
    
    db.commit()


async def get_all_source_gpxs(db: Session) -> List[models.SourceGPX]:
    """
    Get all source GPX routes from database
    
    Args:
        db: Database session
        
    Returns:
        List of SourceGPX models
    """
    return db.query(models.SourceGPX).filter(models.SourceGPX.is_active == True).all()


async def get_source_gpx_by_id(db: Session, source_id: str) -> Optional[models.SourceGPX]:
    """
    Get source GPX by ID
    
    Args:
        db: Database session
        source_id: Source GPX ID
        
    Returns:
        SourceGPX model or None
    """
    return db.query(models.SourceGPX).filter(
        models.SourceGPX.id == source_id,
        models.SourceGPX.is_active == True
    ).first()