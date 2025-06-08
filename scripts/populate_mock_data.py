#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to populate a mock survey with data for development/testing."""

import click
from backend import db
from backend.models import User, Survey, SurveyField, Search, SearchResult, ResultField
import fixtures.surveys
import fixtures.searches
import fixtures.results


def populate_mock_survey(user_id: int, num_searches: int, num_results: int) -> None:
    """Populate database with a mock survey for a specified user."""
    # Verify user exists
    user = User.query.get(user_id)
    if not user:
        click.echo(f"Error: User with ID {user_id} not found", err=True)
        return
    
    click.echo(f"Populating mock survey for user: {user.email_address} (ID: {user_id})")
    
    try:
        # Create one survey with fields
        survey = fixtures.surveys.create_mock_survey(user)
        db.session.add(survey)
        db.session.flush()  # Get survey ID
        
        click.echo(f"Created survey: {survey.name}")
        click.echo(f"  Fields: {len(survey.fields)}")
        
        # Create searches for this survey
        searches = fixtures.searches.create_mock_searches(survey, num_searches)
        for search in searches:
            db.session.add(search)
            db.session.flush()  # Get search ID
            
            click.echo(f"  Created search: {search.name} (query: {search.search_query})")
            
            # Create search results
            results = fixtures.results.create_mock_results(search, survey, num_results)
            for result in results:
                # Add both the image and search result to session
                db.session.add(result.image)
                db.session.add(result)
            
            click.echo(f"    Added {len(results)} search results")
        
        # Commit to get IDs for all results
        db.session.commit()
        
        # Now create duplicate pools across all searches
        click.echo("Creating duplicate pools...")
        all_results = []
        for search in searches:
            search_results = SearchResult.query.filter_by(search_id=search.id_).all()
            all_results.extend(search_results)
        
        fixtures.results.create_duplicate_pools(all_results)
        db.session.commit()
        
        total_results = num_searches * num_results
        duplicates_count = SearchResult.query.filter(SearchResult.duplicate_of_id.isnot(None)).count()
        click.echo(f"\nSuccessfully created:")
        click.echo(f"  - 1 survey with {len(survey.fields)} fields")
        click.echo(f"  - {num_searches} searches")
        click.echo(f"  - {total_results} total search results")
        click.echo(f"  - {duplicates_count} results marked as duplicates with working image URLs")
        
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}", err=True)
        raise


if __name__ == '__main__':
    populate_mock_survey()