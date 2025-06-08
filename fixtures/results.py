"""Mock search result data generators."""

import json
import random
import hashlib
from backend.models import SearchResult, ResultField, Search, Survey, Image


def create_mock_image(search_id: int, result_index: int) -> Image:
    """Create a mock image with fake binary data and hash."""
    mock_image_data = f"MOCK_IMAGE_DATA_{search_id}_{result_index}".encode('utf-8')
    mock_thumbnail_data = f"MOCK_THUMB_{search_id}_{result_index}".encode('utf-8')
    image_hash = hashlib.md5(mock_image_data).hexdigest()
    
    return Image(
        image_file=mock_image_data,
        thumbnail_file=mock_thumbnail_data,
        image_hash=image_hash
    )


def generate_mock_field_value(field, result_index: int) -> str:
    """Generate appropriate mock value based on field type."""
    if field.field_type == "text":
        if field.label == "Species Name":
            # Use the search name if available, fallback to generic
            search_name = getattr(field, '_search_name', 'Wildlife Species')
            return f"{search_name} - Individual {result_index}"
        else:
            return f"Mock notes for result {result_index}"
    
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
        behaviors = ["Feeding", "Nesting", "Flying", "Resting", "Other"]
        return random.choice(behaviors)
    
    elif field.field_type == "radio":
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Windy"]
        return random.choice(weather_conditions)
    
    else:
        return f"Mock value for {field.label}"


def create_mock_result_fields(survey: Survey, search_name: str, result_index: int) -> list[ResultField]:
    """Create mock result fields for all survey fields."""
    result_fields = []
    
    for field in survey.fields:
        # Temporarily attach search name for context-aware field generation
        field._search_name = search_name
        value = generate_mock_field_value(field, result_index)
        
        # Skip some fields randomly to simulate real data (when required field is implemented)
        # if not field.required and random.random() < 0.2:
        #     continue
            
        result_field = ResultField(
            survey_field=field,
            value=value
        )
        result_fields.append(result_field)
    
    return result_fields


def create_mock_search_result(search: Search, image: Image, result_index: int) -> SearchResult:
    """Create a single mock search result with realistic completion state."""
    completion_states = ["complete", "incomplete", "pending"]
    
    return SearchResult(
        search=search,
        image=image,
        direct_link=f"https://example.com/image_{result_index}_direct.jpg",
        visible_link=f"https://example.com/image_{result_index}.jpg",
        image_scraped_state="SUCCESS",
        completion_state=random.choice(completion_states)
    )


def create_mock_image(search_id: int, result_index: int) -> Image:
    """Create a mock image record with binary data and hash."""
    mock_image_data = f"MOCK_IMAGE_DATA_{search_id}_{result_index}".encode('utf-8')
    mock_thumbnail_data = f"MOCK_THUMB_{search_id}_{result_index}".encode('utf-8')
    image_hash = hashlib.md5(mock_image_data).hexdigest()
    
    return Image(
        image_file=mock_image_data,
        thumbnail_file=mock_thumbnail_data,
        image_hash=image_hash
    )


def generate_mock_field_value(field, search: Search, result_index: int) -> str:
    """Generate realistic mock data for a specific survey field."""
    if field.field_type == "text":
        if field.label == "Species Name":
            return f"{search.name} - Individual {result_index}"
        else:
            return f"Mock notes for result {result_index}"
    
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
        behaviors = ["Feeding", "Nesting", "Flying", "Resting", "Other"]
        return random.choice(behaviors)
    
    elif field.field_type == "radio":
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Windy"]
        return random.choice(weather_conditions)
    
    else:
        return f"Mock value for {field.label}"


def create_mock_result_fields(survey: Survey, search: Search, result_index: int) -> list[ResultField]:
    """Create mock result fields for all survey fields."""
    result_fields = []
    
    for field in survey.fields:
        # Skip some fields randomly to simulate real data (when required field is implemented)
        # if not field.required and random.random() < 0.2:
        #     continue
        
        value = generate_mock_field_value(field, search, result_index)
        result_field = ResultField(
            survey_field=field,
            value=value
        )
        result_fields.append(result_field)
    
    return result_fields


def create_mock_search_result(search: Search, image: Image, result_index: int) -> SearchResult:
    """Create a mock search result with realistic completion state."""
    completion_states = ["complete", "incomplete", "pending"]
    
    return SearchResult(
        search=search,
        image=image,
        direct_link=f"https://example.com/image_{result_index}_direct.jpg",
        visible_link=f"https://example.com/image_{result_index}.jpg",
        image_scraped_state="SUCCESS",
        completion_state=random.choice(completion_states)
    )


def create_mock_results(search: Search, survey: Survey, num_results: int = 100) -> list[SearchResult]:
    """Create mock search results with images and field data for the given search."""
    results = []
    
    for i in range(num_results):
        result_index = i + 1
        
        # Create associated mock image
        image = create_mock_image(search.id_, result_index)
        
        # Create search result
        result = create_mock_search_result(search, image, result_index)
        
        # Add mock field responses
        result.result_fields = create_mock_result_fields(survey, search, result_index)
        
        results.append(result)
    
    return results