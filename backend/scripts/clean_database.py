#!/usr/bin/env python
# backend/scripts/clean_database.py
"""
A simple script to clean up the entire database or selected tables.
Use with caution as this will delete data!

Usage:
    python clean_database.py [--all] [--table TABLE_NAME] [--confirm]

Options:
    --all       Clean all tables in the database
    --table     Specify a table to clean (can be used multiple times)
    --confirm   Skip confirmation prompt (useful for automation)
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.append(str(Path(__file__).parent.parent))

# Import database models and configuration from your application
from app.database import SessionLocal, Base, engine
from app.models import User, Activity, ActivityAttempt, Token, SourceGPX, Leaderboard, VerificationToken, AuditLog
from app.core.config import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_separator():
    """Print a separator line"""
    print("-" * 50)

def get_table_count(db, model):
    """Get the count of rows in a table"""
    return db.query(model).count()

def print_table_counts(db):
    """Print the number of rows in each table"""
    print_separator()
    print("CURRENT DATABASE STATE:")
    print_separator()
    
    tables = [
        ("Users", User),
        ("Activities", Activity),
        ("Activity Attempts", ActivityAttempt),
        ("Tokens", Token),
        ("Source GPXs", SourceGPX),
        ("Leaderboard", Leaderboard),
        ("Verification Tokens", VerificationToken),
        ("Audit Logs", AuditLog)
    ]
    
    for name, model in tables:
        count = get_table_count(db, model)
        print(f"{name}: {count} rows")
    
    print_separator()

def clean_table(db, model, name):
    """Clean a specific table"""
    try:
        count_before = get_table_count(db, model)
        # Delete all rows in the table
        db.query(model).delete()
        db.commit()
        print(f"✓ Cleared {count_before} rows from {name}")
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ Error clearing {name}: {str(e)}")
        return False

def clean_all_tables(db, confirm=False):
    """Clean all tables in the database"""
    if not confirm:
        print("WARNING: This will delete ALL data from your database!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Operation cancelled.")
            return

    # Define tables to clean in reverse order of dependencies
    tables = [
        ("Activity Attempts", ActivityAttempt),
        ("Activities", Activity),
        ("Leaderboard", Leaderboard),
        ("Tokens", Token),
        ("Verification Tokens", VerificationToken),
        ("Audit Logs", AuditLog),
        ("Users", User)
        # Note: We don't clear SourceGPX as these are predefined routes
    ]
    
    print_separator()
    print("CLEANING TABLES:")
    print_separator()
    
    success = True
    for name, model in tables:
        if not clean_table(db, model, name):
            success = False
    
    if success:
        print_separator()
        print("✓ Database cleanup completed successfully")
    else:
        print_separator()
        print("⚠ Database cleanup completed with errors")
    
    # Print the current state after cleanup
    print_table_counts(db)

def clean_specific_table(db, table_name, confirm=False):
    """Clean a specific table by name"""
    # Map table names to models
    table_map = {
        "users": User,
        "activities": Activity,
        "activity_attempts": ActivityAttempt,
        "tokens": Token,
        "source_gpxs": SourceGPX,
        "leaderboard": Leaderboard,
        "verification_tokens": VerificationToken,
        "audit_logs": AuditLog
    }
    
    # Convert table_name to lowercase for case-insensitive matching
    table_name_lower = table_name.lower()
    
    if table_name_lower not in table_map:
        print(f"Error: Table '{table_name}' not found.")
        print(f"Available tables: {', '.join(table_map.keys())}")
        return False
    
    if not confirm:
        print(f"WARNING: This will delete ALL data from the '{table_name}' table!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Operation cancelled.")
            return False
    
    model = table_map[table_name_lower]
    display_name = model.__tablename__
    
    print_separator()
    print(f"CLEANING TABLE: {display_name}")
    print_separator()
    
    return clean_table(db, model, display_name)

def main():
    parser = argparse.ArgumentParser(description="Clean up database tables")
    parser.add_argument("--all", action="store_true", help="Clean all tables")
    parser.add_argument("--table", action="append", help="Specify table to clean")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Print current table counts
        print_table_counts(db)
        
        if args.all:
            # Clean all tables
            clean_all_tables(db, args.confirm)
        elif args.table:
            # Clean specific tables
            for table_name in args.table:
                clean_specific_table(db, table_name, args.confirm)
        else:
            # No action specified, show help
            parser.print_help()
    finally:
        # Close the database session
        db.close()

if __name__ == "__main__":
    main()