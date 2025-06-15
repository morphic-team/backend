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
import random
import time
import logging
import warnings
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.sql.expression import func
import threading
from urllib.parse import urlparse
import urllib3

from backend.models import SearchResult, Search
from backend.models import Image as ImageModel
from backend import db


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Suppress urllib3 connection pool warnings
urllib3.disable_warnings(urllib3.exceptions.HTTPWarning)


def mark_image_processing_complete(search_result, success):
    """Update the search result with the processing status."""
    if success:
        search_result.image_scraped_state = SearchResult.ImageScrapedStates.SUCCESS
    else:
        search_result.image_scraped_state = SearchResult.ImageScrapedStates.FAILURE
    
    db.session.add(search_result)
    db.session.commit()


class ImageDownloader:
    """Enhanced image downloader with best_python strategy."""
    
    def __init__(self, max_retries=3, timeout=10, max_connections=100):
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_connections = max_connections
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Initialize session with connection pooling
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _get_browser_headers(self, url):
        """Generate realistic browser headers."""
        parsed = urlparse(url)
        user_agent = random.choice(self.user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Add referrer for hotlink protection bypass
        if parsed.netloc not in ['localhost', '127.0.0.1']:
            headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
        
        # Browser-specific headers based on user agent
        if 'Chrome' in user_agent:
            headers.update({
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            })
        elif 'Firefox' in user_agent:
            headers['Sec-Fetch-Dest'] = 'image'
            headers['Sec-Fetch-Mode'] = 'no-cors'
            headers['Sec-Fetch-Site'] = 'cross-site'
        
        return headers
    
    def download_image(self, url):
        """Download image with retry logic and browser-like headers. Returns content or raises exception."""
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                # Exponential backoff (matching validated algorithm)
                backoff_time = 2 ** (attempt - 1)  # 1s, 2s, 4s
                time.sleep(backoff_time)
            
            # Dynamic timeout increase on retries
            current_timeout = self.timeout * (1 + attempt * 0.5)
            
            try:
                # Fresh headers for each attempt
                headers = self._get_browser_headers(url)
                
                response = self.session.get(
                    url, 
                    headers=headers,
                    timeout=current_timeout, 
                    stream=True,
                    allow_redirects=True
                )
                
                # Handle response scenarios (matching validated design)
                if response.status_code == 200:
                    # Success! Return the content
                    try:
                        return BytesIO(response.content)
                    finally:
                        # Ensure response is closed to free memory (matching validated design)
                        response.close()
                elif response.status_code in [429, 503]:
                    # Rate limiting - retry with backoff (matching validated design)
                    retry_after = response.headers.get('Retry-After')
                    if retry_after and attempt < self.max_retries:
                        try:
                            wait_time = int(retry_after)
                            time.sleep(min(wait_time, 60))  # Cap at 60 seconds
                        except ValueError:
                            pass
                    # Continue to next attempt
                    continue
                else:
                    # Non-200 status code - FAIL immediately (matching validated design)
                    # The validated design does NOT retry 403, 404, 500, etc.
                    raise requests.exceptions.HTTPError(f"HTTP {response.status_code} response", response=response)
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries:
                    raise
                continue
            except requests.exceptions.ConnectionError:
                if attempt == self.max_retries:
                    raise
                continue
            except requests.exceptions.SSLError:
                if attempt == self.max_retries:
                    raise
                continue
            except requests.exceptions.HTTPError:
                # Don't retry HTTP errors, they're permanent
                raise
            except Exception:
                if attempt == self.max_retries:
                    raise
                continue
        
        # Should not reach here, but just in case
        raise requests.exceptions.RequestException("All retry attempts failed")
    
    def cleanup(self):
        """Clean up session resources."""
        if hasattr(self, 'session'):
            self.session.close()


# Global downloader instance (thread-safe)
_downloader = None
_downloader_lock = threading.Lock()

def get_downloader():
    """Get or create the global downloader instance."""
    global _downloader
    if _downloader is None:
        with _downloader_lock:
            if _downloader is None:
                _downloader = ImageDownloader()
    return _downloader


def process_search_result(search_result):
    """Process a single search result: download, process, and check for duplicates."""
    logger.info('Processing search_result %s', search_result.id_)
    
    if not search_result.direct_link:
        logger.warning("Search result %s missing link.", search_result)
        mark_image_processing_complete(search_result, success=False)
        return
    
    # Download image using enhanced downloader
    downloader = get_downloader()
    try:
        raw_image_file = downloader.download_image(search_result.direct_link)
    except Exception as e:
        logger.warning("Failed to fetch image at url %s: %s", search_result.direct_link, str(e))
        mark_image_processing_complete(search_result, success=False)
        return
    
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
    
    try:
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
    finally:
        # Clean up downloader resources
        global _downloader
        if _downloader is not None:
            logger.info("Cleaning up image downloader resources...")
            _downloader.cleanup()
            _downloader = None


# Legacy compatibility
do_work = run_worker