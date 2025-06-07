import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import click
from backend import create_app, db

app = create_app('dev')

@app.cli.command()
def dedup():
    """Remove duplicate search results"""
    from backend.models import SearchResult, Search, Image
    search_results = SearchResult.query.filter(SearchResult.image_scraped_state == 'SUCCESS').limit(100).offset(10000).all()
    for search_result in search_results:
        duplicate_pool = (
            SearchResult.query
            .join(Image)
            .join(Search)
            .filter(Search.survey == search_result.search.survey)
            .filter(Image.image_hash == search_result.image.image_hash)
            .all()
        )
        print(search_result.id_, len(duplicate_pool))

@app.cli.command()
def background_work():
    """Run background work tasks"""
    from backend.background_work import do_work
    with app.app_context():
        do_work()

@app.cli.command()
def create_all():
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        click.echo('Created all tables.')

@app.cli.command()
def drop_all():
    """Drop all database tables"""
    with app.app_context():
        db.drop_all()
        click.echo('Dropped all tables.')

@app.cli.command()
def reload_database():
    """Drop and recreate all database tables"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        click.echo('Reloaded database.')

@app.shell_context_processor
def make_shell_context():
    """Make shell context with models available"""
    from backend.models import Survey, User, Session, SearchResult
    return dict(app=app, db=db, Survey=Survey, User=User, Session=Session, SearchResult=SearchResult)

if __name__ == "__main__":
    app.run()
