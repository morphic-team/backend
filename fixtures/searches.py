"""Mock search data generators."""

from backend.models import Search, Survey


def create_mock_searches(survey: Survey, num_searches: int = 3) -> list[Search]:
    """Create mock searches for the given survey."""
    search_configs = [
        ("Red-tailed Hawk", "red tailed hawk wildlife", "Common hawk species in North America"),
        ("Great Blue Heron", "great blue heron bird", "Large wading bird found near water"),
        ("Barn Owl", "barn owl nocturnal bird", "Nocturnal predator with distinctive face"),
        ("Bald Eagle", "bald eagle american bird", "National bird of the United States"),
        ("Ruby-throated Hummingbird", "ruby throated hummingbird", "Smallest bird in eastern North America"),
    ]
    
    searches = []
    for i in range(min(num_searches, len(search_configs))):
        name, query, comments = search_configs[i]
        search = Search(
            survey=survey,
            name=name,
            search_query=query,
            comments=comments
        )
        searches.append(search)
    
    # If more searches requested than predefined, generate generic ones
    for i in range(len(search_configs), num_searches):
        search = Search(
            survey=survey,
            name=f"Wildlife Search {i+1}",
            search_query=f"wildlife animal search {i+1}",
            comments=f"Generic search number {i+1}"
        )
        searches.append(search)
    
    return searches