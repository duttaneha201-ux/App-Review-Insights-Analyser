"""
URL Validation Service for Google Play Store URLs

This module provides functionality to:
- Validate Play Store URL format
- Extract app ID from URLs
- Verify app existence on Play Store
"""

import re
import logging
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse, parse_qs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class PlayStoreURLValidator:
    """
    Validates Google Play Store URLs and verifies app existence.
    """
    
    # Play Store URL patterns
    PLAY_STORE_DOMAINS = [
        'play.google.com',
        'play.google.com.au',
        'play.google.com.br',
        'play.google.co.uk',
        'play.google.co.in',
        'play.google.co.jp',
        'play.google.co.kr',
        'play.google.co.za',
        'play.google.com.mx',
        'play.google.com.tr',
        'play.google.com.sg',
        'play.google.com.hk',
        'play.google.com.tw',
        'play.google.com.ar',
        'play.google.com.co',
        'play.google.com.pe',
        'play.google.com.ve',
        'play.google.com.cl',
        'play.google.com.ec',
        'play.google.com.uy',
        'play.google.com.py',
        'play.google.com.bo',
        'play.google.com.cr',
        'play.google.com.gt',
        'play.google.com.hn',
        'play.google.com.ni',
        'play.google.com.pa',
        'play.google.com.do',
        'play.google.com.pr',
        'play.google.com.sv',
    ]
    
    # Regex pattern for app ID (package name format: com.example.app)
    # Must have at least 2 segments (e.g., com.example) and start with a letter
    APP_ID_PATTERN = re.compile(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$')
    
    # Timeout settings
    REQUEST_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3
    
    def __init__(self, timeout: int = None, max_retries: int = None):
        """
        Initialize the URL validator.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum number of retries (default: 3)
        """
        self.timeout = timeout or self.REQUEST_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def validate_play_store_url(self, url: str) -> bool:
        """
        Validate if the URL is a valid Google Play Store URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if URL is valid Play Store format, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            parsed = urlparse(url.strip())
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check domain
            domain = parsed.netloc.lower()
            if not any(domain == d or domain.endswith('.' + d) for d in self.PLAY_STORE_DOMAINS):
                return False
            
            # Check path - should contain /store/apps/details
            path = parsed.path.lower()
            if '/store/apps/details' not in path:
                return False
            
            # Check if URL has app ID parameter (id=)
            if 'id=' not in parsed.query:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating URL format: {e}")
            return False
    
    def extract_app_id(self, url: str) -> Optional[str]:
        """
        Extract app ID (package name) from Play Store URL.
        
        Args:
            url: Play Store URL
            
        Returns:
            App ID (package name) if found, None otherwise
        """
        if not self.validate_play_store_url(url):
            return None
        
        try:
            parsed = urlparse(url.strip())
            
            # Method 1: Extract from path /store/apps/details?id=com.example.app
            if 'id=' in parsed.query:
                query_params = parse_qs(parsed.query)
                app_id = query_params.get('id', [None])[0]
                if app_id and self._is_valid_app_id(app_id):
                    return app_id
            
            # Method 2: Extract from path /store/apps/details?id=com.example.app&hl=en
            # Also check for URL-encoded IDs
            path_parts = parsed.path.split('/')
            if 'details' in path_parts:
                idx = path_parts.index('details')
                if idx + 1 < len(path_parts):
                    potential_id = path_parts[idx + 1]
                    if self._is_valid_app_id(potential_id):
                        return potential_id
            
            # Method 3: Try to extract from query string with different formats
            query_params = parse_qs(parsed.query)
            for key in ['id', 'app_id', 'package']:
                if key in query_params:
                    app_id = query_params[key][0]
                    if app_id and self._is_valid_app_id(app_id):
                        return app_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting app ID: {e}")
            return None
    
    def _is_valid_app_id(self, app_id: str) -> bool:
        """
        Validate app ID format (package name).
        
        Args:
            app_id: App ID string to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not app_id or not isinstance(app_id, str):
            return False
        
        # App ID should match package name pattern
        return bool(self.APP_ID_PATTERN.match(app_id.strip()))
    
    def verify_app_exists(self, app_id: str) -> Tuple[bool, Optional[str]]:
        """
        Verify if an app exists on Google Play Store.
        
        Args:
            app_id: App ID (package name) to verify
            
        Returns:
            Tuple of (exists: bool, error_message: Optional[str])
            - exists: True if app exists, False otherwise
            - error_message: Error message if verification failed, None if successful
        """
        if not app_id or not self._is_valid_app_id(app_id):
            return False, "Invalid app ID format"
        
        # Construct Play Store URL
        play_store_url = f"https://play.google.com/store/apps/details?id={app_id}"
        
        try:
            response = self.session.get(
                play_store_url,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Check status code
            if response.status_code == 200:
                # Check if page contains app details (not error page)
                content = response.text.lower()
                
                # Indicators that app exists:
                # - Contains app title/name
                # - Contains rating information
                # - Contains "Install" button or app details
                # - Does NOT contain specific error messages
                
                # More specific error indicators (avoid false positives from URLs/scripts)
                error_patterns = [
                    "we're sorry, the requested url was not found",
                    "this app is not available",
                    "app not found on this server",
                    "the page you requested was not found",
                ]
                
                # Check for specific error messages (not just "404" or "not found" which can appear in URLs)
                has_error_message = any(
                    pattern in content for pattern in error_patterns
                ) or (
                    'not found' in content and 
                    ('we\'re sorry' in content or 'the requested' in content or 'this app is not available' in content)
                )
                
                success_indicators = [
                    'itemprop="name"',
                    'aria-label="install"',
                    'data-testid="install-button"',
                    'class="rating"',
                    'itemprop="aggregateRating"',
                    'itemprop="applicationCategory"',
                ]
                
                # Check for success indicators
                has_success_indicators = any(indicator in content for indicator in success_indicators)
                
                # If we have clear error messages, app doesn't exist
                if has_error_message and not has_success_indicators:
                    return False, "App not found on Play Store"
                
                # If we have success indicators, app exists
                if has_success_indicators:
                    return True, None
                
                # If we can't determine, assume it exists (conservative approach)
                # But log a warning
                logger.warning(f"Could not definitively verify app existence for {app_id}")
                return True, None
                
            elif response.status_code == 404:
                return False, "App not found on Play Store (404)"
            elif response.status_code == 403:
                return False, "Access forbidden - may be region-restricted or require authentication"
            elif response.status_code == 429:
                return False, "Rate limit exceeded - too many requests"
            else:
                return False, f"Unexpected status code: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, f"Request timeout after {self.timeout} seconds"
        except requests.exceptions.ConnectionError:
            return False, "Connection error - could not reach Play Store"
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception while verifying app: {e}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error while verifying app: {e}")
            return False, f"Unexpected error: {str(e)}"
    
    def validate_and_verify(self, url: str) -> Dict[str, any]:
        """
        Complete validation: check URL format and verify app existence.
        
        Args:
            url: Play Store URL to validate and verify
            
        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'app_id': Optional[str],
                'app_exists': Optional[bool],
                'error': Optional[str],
                'app_name': Optional[str]  # Could be extracted in future
            }
        """
        result = {
            'valid': False,
            'app_id': None,
            'app_exists': None,
            'error': None,
            'app_name': None
        }
        
        # Step 1: Validate URL format
        if not self.validate_play_store_url(url):
            result['error'] = "Invalid Play Store URL format"
            return result
        
        result['valid'] = True
        
        # Step 2: Extract app ID
        app_id = self.extract_app_id(url)
        if not app_id:
            result['error'] = "Could not extract app ID from URL"
            return result
        
        result['app_id'] = app_id
        
        # Step 3: Verify app exists
        exists, error = self.verify_app_exists(app_id)
        result['app_exists'] = exists
        if error:
            result['error'] = error
        
        return result


def validate_play_store_url(url: str) -> bool:
    """
    Convenience function to validate Play Store URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    validator = PlayStoreURLValidator()
    return validator.validate_play_store_url(url)


def extract_app_id(url: str) -> Optional[str]:
    """
    Convenience function to extract app ID from URL.
    
    Args:
        url: Play Store URL
        
    Returns:
        App ID if found, None otherwise
    """
    validator = PlayStoreURLValidator()
    return validator.extract_app_id(url)


def verify_app_exists(app_id: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to verify app existence.
    
    Args:
        app_id: App ID to verify
        
    Returns:
        Tuple of (exists: bool, error_message: Optional[str])
    """
    validator = PlayStoreURLValidator()
    return validator.verify_app_exists(app_id)

