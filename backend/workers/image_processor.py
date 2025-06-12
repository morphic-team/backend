"""
Image processing worker that downloads and processes images from search results.

This worker runs continuously, picking up unprocessed search results and:
1. Downloads the image from the direct link
2. Generates a perceptual hash for duplicate detection
3. Creates thumbnail version
4. Marks duplicates within the same survey
"""
import socket
from io import BytesIO
from PIL import Image
import imagehash
import requests
import logging
import warnings
from time import sleep
from sqlalchemy.sql.expression import func

from backend.models import SearchResult, Search
from backend.models import Image as ImageModel
from backend import db


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def mark_image_processing_complete(search_result, success):
    """Update the search result with the processing status."""
    if success:
        search_result.image_scraped_state = SearchResult.ImageScrapedStates.SUCCESS
    else:
        search_result.image_scraped_state = SearchResult.ImageScrapedStates.FAILURE
    
    db.session.add(search_result)
    db.session.commit()


def process_search_result(search_result):
    """Process a single search result: download, process, and check for duplicates."""
    logger.info('Processing search_result %s', search_result.id_)
    
    if not search_result.direct_link:
        logger.warning("Search result %s missing link.", search_result)
        mark_image_processing_complete(search_result, success=False)
        return
    
    # Download image
    try:
        raw_image_response = requests.get(search_result.direct_link, timeout=10)
    except (requests.exceptions.RequestException, socket.timeout):
        logger.warning("Timeout fetching image at url %s.", search_result.direct_link)
        mark_image_processing_complete(search_result, success=False)
        return
    
    if raw_image_response.status_code != 200:
        logger.warning(
            "Search result %s image link %s returned non 200 response.",
            search_result, search_result.direct_link
        )
        mark_image_processing_complete(search_result, success=False)
        return
    
    raw_image_file = BytesIO(raw_image_response.content)
    
    # Process image
    warnings.simplefilter('error', Image.DecompressionBombWarning)
    try:
        image = Image.open(raw_image_file)
        
        # Generate perceptual hash for duplicate detection
        image_hash = imagehash.phash(image)
        
        # Convert to RGB and save full size
        image = image.convert('RGB')
        image_file = BytesIO()
        image.save(image_file, 'JPEG')
        
        # Create thumbnail
        image.thumbnail((500, 500), Image.Resampling.LANCZOS)
        thumbnail_file = BytesIO()
        image.save(thumbnail_file, 'JPEG')
        
        search_result.image = ImageModel(
            image_file=image_file.getvalue(),
            thumbnail_file=thumbnail_file.getvalue(),
            image_hash=str(image_hash),
        )
    except (IOError, Image.DecompressionBombWarning):
        logger.warning("Issue with PIL processing image.")
        mark_image_processing_complete(search_result, success=False)
        return
    
    # Check for duplicates within the same survey
    canonical_result = (
        SearchResult.query
        .join(ImageModel)
        .join(Search)
        .filter(Search.survey == search_result.search.survey)
        .filter(ImageModel.image_hash == search_result.image.image_hash)
        .filter(SearchResult.duplicate_of_id.is_(None))  # Find the canonical (not a duplicate itself)
        .filter(SearchResult.id_ != search_result.id_)  # Exclude current result
        .first()
    )
    
    if canonical_result:
        logger.warning("Marking as duplicate: %s -> canonical: %s", search_result, canonical_result)
        search_result.completion_state = SearchResult.CompletionStates.NOT_USABLE
        search_result.duplicate_of_id = canonical_result.id_
    
    mark_image_processing_complete(search_result, success=True)


def run_worker():
    """Main worker loop - continuously processes unscraped search results."""
    logger.info("Starting image processing worker")
    
    while True:
        # Get a random unprocessed search result
        unscraped_search_result = (
            SearchResult.query
            .filter(SearchResult.image_scraped_state == 'NEW')
            .order_by(func.random())
            .first()
        )
        
        if unscraped_search_result is None:
            logger.info('No unprocessed results, sleeping...')
            sleep(5)
            continue
        
        process_search_result(unscraped_search_result)


# Legacy compatibility
do_work = run_worker