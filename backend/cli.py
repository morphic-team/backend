"""
Flask CLI commands for the Morphic backend.
"""
import click
from backend import db


def register_commands(app):
    """Register CLI commands with the Flask app."""
    
    @app.cli.command()
    @click.option('--threads', default=1, type=int, help='Number of worker threads (default: 1)')
    def run_worker(threads):
        """Run the image processing worker."""
        from backend.workers.image_processor import run_worker
        run_worker(num_threads=threads)
    
    @app.cli.command()
    @click.option('--user-id', required=True, type=int, help='User ID to populate mock survey for')
    @click.option('--num-searches', default=3, help='Number of searches to create (default: 3)')
    @click.option('--num-results', default=100, help='Number of results per search (default: 100)')
    def populate_mock_survey(user_id: int, num_searches: int, num_results: int) -> None:
        """Populate database with a mock survey for a specified user."""
        from scripts.populate_mock_data import populate_mock_survey
        populate_mock_survey(user_id, num_searches, num_results)
    
    @app.shell_context_processor
    def make_shell_context():
        """Make shell context with models available."""
        from backend.models import Survey, User, Session, SearchResult
        return dict(app=app, db=db, Survey=Survey, User=User, Session=Session, SearchResult=SearchResult)