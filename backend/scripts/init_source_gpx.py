#!/usr/bin/env python
# backend/scripts/init_source_gpx.py
"""
Script to initialize source GPX files in the database.
This script reads all GPX files from the configured GPX_PATH and adds them to the database
if they don't already exist.

Usage:
    python init_source_gpx.py [--force]

Options:
    --force     Force update of existing entries
"""

import argparse
import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add the parent directory to sys.path to import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import SourceGPX
from app.services.source_gpx_service import get_source_gpx_info, list_available_source_gpx_files
from app.core.config import settings

async def init_source_gpx_database(force=False):
    """
    Initialize source GPX database from files
    
    Args:
        force: Force update of existing entries
    """
    print(f"Initializing source GPX database from {settings.SOURCE_GPX_PATH}")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # List available GPX files
        files = await list_available_source_gpx_files()
        print(f"Found {len(files)} GPX files: {', '.join(files)}")
        
        if not files:
            print(f"No GPX files found in {settings.SOURCE_GPX_PATH}")
            print(f"Please add GPX files to this directory and run the script again.")
            return
        
        for filename in files:
            # Check if already in database
            existing = db.query(SourceGPX).filter(SourceGPX.filename == filename).first()
            
            if existing and not force:
                print(f"Skipping {filename} - already in database (use --force to update)")
                continue
                
            # Get info for new file
            print(f"Processing {filename}...")
            info = await get_source_gpx_info(filename)
            
            if "error" in info:
                print(f"Error processing {filename}: {info['error']}")
                continue
            
            if existing and force:
                # Update existing record
                print(f"Updating existing entry for {filename}")
                existing.name = info.get("name", "Unnamed Route")
                existing.description = info.get("description", "")
                existing.distance = info.get("distance_meters", 0)
                existing.is_active = True
                existing.updated_at = datetime.now()
            else:
                # Add new record
                print(f"Adding new entry for {filename}")
                new_source = SourceGPX(
                    id=uuid.uuid4(),
                    name=info.get("name", "Unnamed Route"),
                    description=info.get("description", ""),
                    filename=filename,
                    distance=info.get("distance_meters", 0),
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(new_source)
            
        # Commit changes
        db.commit()
        print("Database initialization complete!")
        
        # Print summary of source GPXs in database
        sources = db.query(SourceGPX).all()
        print(f"\nSource GPXs in database ({len(sources)}):")
        for source in sources:
            print(f"  - {source.name} ({source.filename}): {source.distance/1000:.1f}km, Active: {source.is_active}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Initialize source GPX files in the database")
    parser.add_argument("--force", action="store_true", help="Force update of existing entries")
    
    args = parser.parse_args()
    
    asyncio.run(init_source_gpx_database(args.force))

if __name__ == "__main__":
    main()