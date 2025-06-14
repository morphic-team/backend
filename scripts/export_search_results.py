#!/usr/bin/env python
"""
Export SearchResult data for baseline download testing analysis.

This script exports all SearchResult records to CSV for systematic testing
of image download success rates and failure patterns.
"""

import os
import sys
import csv
import argparse
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from backend import create_app, db
from backend.models import SearchResult, Search, Survey, User


def export_search_results(output_file, limit=None, include_processed=True):
    """
    Export SearchResult data to CSV for analysis.
    
    Args:
        output_file (str): Path to output CSV file
        limit (int): Maximum number of records to export (None for all)
        include_processed (bool): Include results that were already processed
    """
    
    app = create_app()
    
    with app.app_context():
        # Build query
        query = (
            SearchResult.query
            .join(Search)
            .join(Survey)
            .join(User)
        )
        
        if not include_processed:
            # Only include results that haven't been successfully processed
            query = query.filter(
                SearchResult.image_scraped_state.in_(['NEW', 'STARTED', 'FAILURE'])
            )
        
        if limit:
            query = query.limit(limit)
        
        results = query.all()
        
        print(f"Exporting {len(results)} SearchResult records...")
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'search_result_id',
                'survey_id', 
                'search_id',
                'user_id',
                'visible_link',
                'direct_link',
                'image_scraped_state',
                'completion_state',
                'duplicate_of_id',
                'survey_name',
                'search_query',
                'created_at'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'search_result_id': result.id_,
                    'survey_id': result.search.survey.id_,
                    'search_id': result.search.id_,
                    'user_id': result.search.survey.user.id_,
                    'visible_link': result.visible_link,
                    'direct_link': result.direct_link,
                    'image_scraped_state': result.image_scraped_state,
                    'completion_state': result.completion_state,
                    'duplicate_of_id': result.duplicate_of_id,
                    'survey_name': result.search.survey.name,
                    'search_query': result.search.query,
                    'created_at': result.created_at.isoformat() if hasattr(result, 'created_at') and result.created_at else ''
                })
        
        print(f"Export complete: {output_file}")
        
        # Print summary statistics
        total_count = len(results)
        state_counts = {}
        
        for result in results:
            state = result.image_scraped_state
            state_counts[state] = state_counts.get(state, 0) + 1
        
        print(f"\nSummary Statistics:")
        print(f"Total records: {total_count}")
        print(f"Image scraped states:")
        for state, count in sorted(state_counts.items()):
            percentage = (count / total_count) * 100
            print(f"  {state}: {count} ({percentage:.1f}%)")


def get_database_stats():
    """Print database statistics for context."""
    
    app = create_app()
    
    with app.app_context():
        total_results = SearchResult.query.count()
        total_searches = Search.query.count()
        total_surveys = Survey.query.count()
        total_users = User.query.count()
        
        print(f"Database Statistics:")
        print(f"Total SearchResults: {total_results:,}")
        print(f"Total Searches: {total_searches:,}")
        print(f"Total Surveys: {total_surveys:,}")
        print(f"Total Users: {total_users:,}")
        
        # Breakdown by processing state
        state_counts = (
            db.session.query(SearchResult.image_scraped_state, db.func.count(SearchResult.id_))
            .group_by(SearchResult.image_scraped_state)
            .all()
        )
        
        print(f"\nProcessing State Breakdown:")
        for state, count in state_counts:
            percentage = (count / total_results) * 100
            print(f"  {state}: {count:,} ({percentage:.1f}%)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export SearchResult data for download testing')
    parser.add_argument('--output', '-o', default=f'search_results_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        help='Output CSV file path')
    parser.add_argument('--limit', '-l', type=int, help='Maximum number of records to export')
    parser.add_argument('--exclude-processed', action='store_true', 
                        help='Exclude already successfully processed results')
    parser.add_argument('--stats-only', action='store_true',
                        help='Only show database statistics, do not export')
    
    args = parser.parse_args()
    
    if args.stats_only:
        get_database_stats()
    else:
        get_database_stats()
        print()
        export_search_results(
            args.output, 
            limit=args.limit,
            include_processed=not args.exclude_processed
        )