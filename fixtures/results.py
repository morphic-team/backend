"""Mock search result data generators."""

import json
import random
import hashlib
from backend.models import SearchResult, ResultField, Search, Survey, Image


def generate_placeholder_url() -> tuple[str, str]:
    """Generate placeholder URLs with random colors for both background and text."""
    colors = ['FF0000', '00FF00', '0000FF', 'FFFF00', 'FF00FF', '00FFFF', 
              '800000', '008000', '000080', '808000', '800080', '008080',
              'FFA500', 'A52A2A', '808080', '000000', 'FFFFFF', 'DC143C']
    
    bg_color = random.choice(colors)
    text_color = random.choice([c for c in colors if c != bg_color])
    
    base_url = f"https://placehold.co/600x400/{bg_color}/{text_color}.jpg"
    return base_url, base_url  # Use same for both visible and direct


def generate_realistic_completion_state(result_index: int, total_results: int) -> str:
    """Generate realistic completion states with pattern: early results more complete."""
    progress = result_index / total_results
    
    if progress < 0.3:  # First 30% - mostly complete
        return random.choices(
            ['DONE', 'NOT_USABLE', 'REVISIT'],
            weights=[70, 20, 10]
        )[0]
    elif progress < 0.6:  # Middle 30% - mixed
        return random.choices(
            ['DONE', 'REVISIT', 'NOT_USABLE'],
            weights=[40, 50, 10]
        )[0]
    else:  # Last 40% - mostly need review
        return random.choices(
            ['REVISIT', 'DONE', 'NOT_USABLE'],
            weights=[80, 15, 5]
        )[0]


def generate_realistic_processing_state(result_index: int) -> str:
    """Generate realistic processing states - most should be SUCCESS."""
    return random.choices(
        ['SUCCESS', 'NEW', 'STARTED', 'FAILURE'],
        weights=[85, 8, 4, 3]
    )[0]


def create_duplicate_pools(results: list[SearchResult]) -> None:
    """Create duplicate relationships by grouping some results into pools."""
    # Create pools of various sizes
    pool_sizes = [2, 2, 3, 4, 2, 3]  # Mix of different duplicate pool sizes
    
    available_results = [r for r in results if r.completion_state != 'NOT_USABLE']
    random.shuffle(available_results)
    
    pool_start = 0
    for pool_size in pool_sizes:
        if pool_start + pool_size > len(available_results):
            break
            
        # Get the pool of results
        pool = available_results[pool_start:pool_start + pool_size]
        if len(pool) < 2:
            break
            
        # First result becomes canonical, others become duplicates
        canonical = pool[0]
        duplicates = pool[1:]
        
        # Make all images in the pool have the same hash (simulating duplicates)
        canonical_hash = canonical.image.image_hash
        for duplicate in duplicates:
            duplicate.image.image_hash = canonical_hash
            duplicate.completion_state = 'NOT_USABLE'
            duplicate.duplicate_of_id = canonical.id_
        
        pool_start += pool_size


def create_mock_image(search_id: int, result_index: int, image_hash: str = None) -> Image:
    """Create a mock image with realistic binary data and hash."""
    mock_image_data = f"MOCK_IMAGE_DATA_{search_id}_{result_index}".encode('utf-8')
    mock_thumbnail_data = f"MOCK_THUMB_{search_id}_{result_index}".encode('utf-8')
    
    if image_hash:
        # Use provided hash for duplicates
        final_hash = image_hash
    else:
        # Generate unique hash
        final_hash = hashlib.md5(mock_image_data).hexdigest()[:16]  # Shorter for readability
    
    return Image(
        image_file=mock_image_data,
        thumbnail_file=mock_thumbnail_data,
        image_hash=final_hash
    )


def generate_mock_field_value(field, search: Search, result_index: int) -> str:
    """Generate realistic mock data for a specific survey field."""
    if field.field_type == "text":
        if "species" in field.label.lower() or "name" in field.label.lower():
            return f"{search.name} - Individual {result_index}"
        else:
            notes = [
                f"Observed during morning hours. Individual {result_index} appeared healthy.",
                f"Result {result_index}: Good visibility, clear identification possible.",
                f"Individual {result_index} showed typical behavior patterns.",
                f"Clear sighting #{result_index} with good photographic conditions.",
                f"Result {result_index}: Weather conditions were favorable for observation."
            ]
            return random.choice(notes)
    
    elif field.field_type == "location":
        # Generate coordinates around different global regions
        regions = [
            (37.7749, -122.4194),  # San Francisco
            (40.7128, -74.0060),   # New York
            (51.5074, -0.1278),    # London
            (-33.8688, 151.2093),  # Sydney
            (35.6762, 139.6503),   # Tokyo
        ]
        base_lat, base_lng = random.choice(regions)
        lat = base_lat + random.uniform(-0.5, 0.5)
        lng = base_lng + random.uniform(-0.5, 0.5)
        return json.dumps({
            "latitude": round(lat, 6),
            "longitude": round(lng, 6)
        })
    
    elif field.field_type == "select":
        behaviors = ["Feeding", "Nesting", "Flying", "Resting", "Hunting", "Other"]
        return random.choice(behaviors)
    
    elif field.field_type == "radio":
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Windy", "Foggy"]
        return random.choice(weather_conditions)
    
    else:
        return f"Mock value for {field.label}"


def create_mock_result_fields(survey: Survey, search: Search, result_index: int) -> list[ResultField]:
    """Create mock result fields for all survey fields."""
    result_fields = []
    
    for field in survey.fields:
        # Skip some fields occasionally to simulate real incomplete data
        if random.random() < 0.05:  # 5% chance to skip non-essential fields
            continue
        
        value = generate_mock_field_value(field, search, result_index)
        result_field = ResultField(
            survey_field=field,
            value=value
        )
        result_fields.append(result_field)
    
    return result_fields


def create_mock_search_result(search: Search, image: Image, result_index: int, total_results: int) -> SearchResult:
    """Create a mock search result with realistic states and working image URLs."""
    visible_link, direct_link = generate_placeholder_url()
    
    return SearchResult(
        search=search,
        image=image,
        direct_link=direct_link,
        visible_link=visible_link,
        image_scraped_state=generate_realistic_processing_state(result_index),
        completion_state=generate_realistic_completion_state(result_index, total_results)
    )


def create_mock_results(search: Search, survey: Survey, num_results: int = 100) -> list[SearchResult]:
    """Create mock search results with realistic data, working images, and duplicate pools."""
    results = []
    
    # Create all results first
    for i in range(num_results):
        result_index = i + 1
        
        # Create associated mock image (no hash yet, will be set later for duplicates)
        image = create_mock_image(search.id_, result_index)
        
        # Create search result with realistic states
        result = create_mock_search_result(search, image, result_index, num_results)
        
        # Add mock field responses
        result.result_fields = create_mock_result_fields(survey, search, result_index)
        
        results.append(result)
    
    # After creating all results, set up duplicate pools
    # Note: This will be called after the results are saved to DB so they have IDs
    
    return results