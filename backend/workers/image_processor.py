"""
Image processing worker that downloads and processes images from search results.

This worker runs continuously, picking up unprocessed search results and:
1. Downloads the image from the direct link
2. Generates a perceptual hash for duplicate detection
3. Creates thumbnail version
4. Marks duplicates within the same survey

Supports multi-threading with PostgreSQL row-level locking to prevent race conditions.
"""
import socket
from io import BytesIO
from PIL import Image
import imagehash
import requests
import logging
import warnings
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.sql.expression import func
import threading

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


def get_next_work_item():
    """
    Atomically claim the next unprocessed search result using PostgreSQL row-level locking.
    
    Uses SELECT FOR UPDATE SKIP LOCKED to ensure multiple workers can run concurrently
    without race conditions. Each worker will get a different row to process.
    """
    try:
        # Start a transaction and lock a row for this worker
        search_result = (
            SearchResult.query
            .filter(SearchResult.image_scraped_state == 'NEW')
            .order_by(func.random())  # Randomize to spread work across surveys
            .with_for_update(skip_locked=True)  # Skip rows locked by other workers
            .first()
        )
        
        if search_result:
            # Mark as STARTED to claim it (even if processing fails, we won't retry immediately)
            search_result.image_scraped_state = SearchResult.ImageScrapedStates.STARTED
            db.session.commit()
            return search_result
        
        return None
    except Exception as e:
        logger.error("Error claiming work item: %s", e)
        db.session.rollback()
        return None


def worker_thread(app):
    """Single worker thread that continuously processes search results."""
    thread_id = threading.current_thread().name
    logger.info("Starting worker thread %s", thread_id)
    
    # Each thread needs its own application context
    with app.app_context():
        while True:
            # Atomically claim the next work item
            search_result = get_next_work_item()
            
            if search_result is None:
                sleep(5)  # No work available, sleep and retry
                continue
            
            logger.info("Thread %s processing search_result %s", thread_id, search_result.id_)
            process_search_result(search_result)


def run_worker(num_threads=1):
    """
    Run the image processing worker with specified number of threads.
    
    Args:
        num_threads (int): Number of worker threads to run concurrently (default: 1)
    """
    from flask import current_app
    
    logger.info("Starting image processing worker with %d threads", num_threads)
    app = current_app._get_current_object()  # Get the actual app instance
    
    if num_threads == 1:
        # Single-threaded mode - run directly
        worker_thread(app)
    else:
        # Multi-threaded mode using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=num_threads, thread_name_prefix="ImageWorker") as executor:
            # Submit worker threads with app instance
            futures = [executor.submit(worker_thread, app) for _ in range(num_threads)]
            
            try:
                # Wait for all threads (they run indefinitely)
                for future in as_completed(futures):
                    future.result()  # This will raise any exceptions
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down workers...")
                executor.shutdown(wait=True)


# Legacy compatibility
do_work = run_worker