
import click
from backend import create_app, db
import scripts.populate_mock_data

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
@click.option('--user-id', required=True, type=int, help='User ID to populate mock survey for')
@click.option('--num-searches', default=3, help='Number of searches to create (default: 3)')
@click.option('--num-results', default=100, help='Number of results per search (default: 100)')
def populate_mock_survey(user_id: int, num_searches: int, num_results: int) -> None:
    """Populate database with a mock survey for a specified user"""
    with app.app_context():
        scripts.populate_mock_data.populate_mock_survey(user_id, num_searches, num_results)

@app.shell_context_processor
def make_shell_context():
    """Make shell context with models available"""
    from backend.models import Survey, User, Session, SearchResult
    return dict(app=app, db=db, Survey=Survey, User=User, Session=Session, SearchResult=SearchResult)

if __name__ == "__main__":
    app.run()
