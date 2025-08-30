import json
import os
import datetime
import asyncio
import hashlib
import base64
import secrets
import urllib.parse
import requests
import logging
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any, Callable
from config import ENVIRONMENT
from Functions.telegram_notifier import send_to_phone


# Set up logger
logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self):
        self.environment = ENVIRONMENT
        # Create tokens directory if it doesn't exist
        self.tokens_dir = "tokens"
        if not os.path.exists(self.tokens_dir):
            os.makedirs(self.tokens_dir)
        
        self.tokens_file = os.path.join(self.tokens_dir, f"tokens_{self.environment}.json")
        self.tokens = self._load_tokens()
        
        # Auth URLs based on environment
        if ENVIRONMENT == "production":
            self.auth_base_url = "https://atlas-auth.rickshawnetwork.com"
            self.redirect_uri = "https://atlas.rickshawnetwork.com"
        else:
            self.auth_base_url = "https://staging-atlas-auth.rickshawnetwork.com"
            self.redirect_uri = "https://staging-atlas.rickshawnetwork.com"
    
    def _load_tokens(self) -> list:
        """Load tokens from JSON file"""
        if os.path.exists(self.tokens_file):
            try:
                with open(self.tokens_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_tokens(self):
        """Save tokens to JSON file"""
        with open(self.tokens_file, 'w') as f:
            json.dump(self.tokens, f, indent=2)
    
    def _get_next_id(self) -> int:
        """Get the next available ID"""
        if not self.tokens:
            return 1
        return max(token['id'] for token in self.tokens) + 1
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format (YYYY-MM-DDTHH:MM:SS)"""
        return datetime.datetime.now().isoformat()
    
    def _is_token_expired_by_age(self, token: Dict[str, Any], max_age_hours: int = 48) -> bool:
        """Check if token is expired based on age (48 hours = 2 days)"""
        if not token.get('active_from'):
            return True
        
        try:
            token_time = datetime.datetime.fromisoformat(token['active_from'])
            age = datetime.datetime.now() - token_time
            return age.total_seconds() > (max_age_hours * 3600)
        except (ValueError, TypeError):
            return True
    
    def _generate_pkce(self):
        """Generate PKCE code verifier and challenge"""
        code_verifier = secrets.token_urlsafe(64)[:128]
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b'=').decode('utf-8')
        return code_verifier, code_challenge
    
    async def _generate_new_token_async(self) -> Optional[Dict[str, str]]:
        """Generate a new access token and refresh token using Playwright"""
        logger.info("Generating new access token...")
        
        code_verifier, code_challenge = self._generate_pkce()
        client_id = 'Atlas_App'
        auth_url = (
            f'{self.auth_base_url}/connect/authorize?'
            + urllib.parse.urlencode({
                'client_id': client_id,
                'response_type': 'code',
                'scope': 'openid profile email offline_access',
                'redirect_uri': self.redirect_uri,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',
            })
        )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(auth_url)
            await page.wait_for_load_state('networkidle')
            
            # Click the Azure AD/OpenId button
            try:
                azure_button = await page.wait_for_selector('button[name="provider"][value="AzureOpenId"]', timeout=10000)
            except Exception:
                logger.error("Azure AD/OpenId button not found.")
                await browser.close()
                return None
                
            await azure_button.click()
            await page.wait_for_load_state('networkidle')
            
            # Now on Microsoft login page, fill in credentials
            try:
                await page.wait_for_selector('input[type="email"]', timeout=15000)
                email = os.getenv('ATLAS_USERNAME')
                await page.fill('input[type="email"]', email)
                try:
                    await page.click('input[type="submit"]')
                except Exception:
                    await page.click('button[type="submit"]')
                await page.wait_for_selector('input[type="password"]', timeout=15000)
                password = os.getenv('ATLAS_PASSWORD')
                await page.fill('input[type="password"]', password)
                try:
                    await page.click('input[type="submit"]')
                except Exception:
                    await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
            except Exception:
                logger.error("Microsoft login form not found or failed.")
                await browser.close()
                return None
                
            # MFA handling (minimal, just try to click approve if present)
            try:
                approve_selectors = [
                    'div[role="button"]:has-text("Approve a request on my Microsoft Authenticator app")',
                    'div[data-test-id="auth-app-approve"]',
                    'button:has-text("Approve a request on my Microsoft Authenticator app")',
                ]
                for selector in approve_selectors:
                    try:
                        approve_button = await page.query_selector(selector)
                        if approve_button:
                            await approve_button.click()
                            await page.wait_for_load_state('networkidle')
                            break
                    except Exception:
                        continue
            except Exception:
                pass
                
            # Print MFA number if present
            try:
                number_element = await page.wait_for_selector('#idRichContext_DisplaySign', timeout=5000)
                number_text = await number_element.inner_text()
                import re
                match = re.search(r'\b\d{2}\b', number_text)
                if match:
                    logger.info(f"[MFA] Number on page: {match.group()}")
                    # USE telegram notifier to send the number to the phone
                    send_to_phone(f"[MFA] Number on page: {match.group()}") # Send to phone
                else:
                    logger.warning(f"Could not find a 2-digit number in the extracted text: '{number_text}'")
            except Exception as e:
                logger.error(f"Could not extract MFA number from the page: {e}")
                
            # Wait for redirect with code
            code_found = None
            def handle_url_change(url):
                nonlocal code_found
                parsed = urllib.parse.urlparse(url)
                code = urllib.parse.parse_qs(parsed.query).get('code', [None])[0]
                if code:
                    code_found = code
            page.on('framenavigated', lambda frame: handle_url_change(frame.url))
            await page.wait_for_url(lambda url: 'code=' in url, timeout=60000)
            if code_found:
                code = code_found
            else:
                code = urllib.parse.parse_qs(urllib.parse.urlparse(page.url).query).get('code', [None])[0]
            await browser.close()
            
        if not code:
            logger.error("Authorization code not found.")
            return None
            
        token_url = f'{self.auth_base_url}/connect/token'
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier,
            'client_id': client_id,
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        response = requests.post(token_url, data=data, headers=headers)
        if response.status_code != 200:
            logger.error(f"Token request failed: {response.text}")
            return None
        token_response = response.json()
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')  # Capture refresh token
        
        if access_token and refresh_token:
            # Store the new token and deactivate old ones
            token_id = self.add_token(access_token, refresh_token)
            logger.info(f"Access token stored with ID: {token_id}")
            return {'access_token': access_token, 'refresh_token': refresh_token}
        else:
            logger.error("No access token or refresh token received from the server.")
            return None
    
    def _generate_new_token(self) -> Optional[Dict[str, str]]:
        """Synchronous wrapper for async token generation"""
        try:
            return asyncio.run(self._generate_new_token_async())
        except Exception as e:
            logger.error(f"Error generating new token: {e}")
            return None
    
    def add_token(self, access_value: str, refresh_value: str) -> int:
        """Add a new token (access + refresh) and deactivate old ones"""
        # Deactivate all existing tokens
        for token in self.tokens:
            token['active'] = False
        
        # Create new token with new ID
        new_token = {
            'id': self._get_next_id(),
            'active': True,
            'value': access_value,
            'refresh_token': refresh_value,
            'active_from': self._get_current_timestamp(),
            'last_used': self._get_current_timestamp(),
            'usage': 1
        }
        
        self.tokens.append(new_token)
        self._save_tokens()
        return new_token['id']
    
    def update_existing_token(self, access_value: str, refresh_value: str = None) -> bool:
        """Update existing active token (used for refresh operations)"""
        active_tokens = [token for token in self.tokens if token['active']]
        if not active_tokens:
            return False
        
        active_token = max(active_tokens, key=lambda x: x['id'])
        active_token['value'] = access_value
        if refresh_value:
            active_token['refresh_token'] = refresh_value
        active_token['last_used'] = self._get_current_timestamp()
        active_token['active_from'] = self._get_current_timestamp()  # Reset age counter
        
        logger.info(f"Updated token ID {active_token['id']} with new access token length: {len(access_value)}")
        logger.info(f"Token active_from reset to: {active_token['active_from']}")
        
        self._save_tokens()
        return True
    
    def get_active_token_value(self) -> Optional[str]:
        """Get the active access token value, checking age first (2 days)"""
        active_tokens = [token for token in self.tokens if token['active']]
        
        if not active_tokens:
            return None
        
        # Get the most recent active token (highest ID)
        active_token = max(active_tokens, key=lambda x: x['id'])
        
        # Check if token is too old (48 hours = 2 days)
        if self._is_token_expired_by_age(active_token, max_age_hours=24):
            logger.info(f"Token ID {active_token['id']} is older than 2 days, attempting to refresh it...")
            
            # First try to refresh using refresh token (no MFA needed)
            if self._refresh_token():
                logger.info("Token refreshed successfully using refresh token")
                # Get the updated token - it should now have a new active_from timestamp
                active_tokens = [token for token in self.tokens if token['active']]
                active_token = max(active_tokens, key=lambda x: x['id'])
                logger.info(f"Now using refreshed token ID {active_token['id']} with new active_from: {active_token['active_from']}")
            else:
                logger.warning("Refresh token failed, generating new token via browser...")
                # Fall back to browser automation (MFA required)
                new_tokens = self._generate_new_token()
                if new_tokens:
                    return new_tokens['access_token']
                else:
                    logger.error("Failed to generate new token")
                    return None
        
        logger.info(f"Returning active token ID {active_token['id']} (age: {self._get_token_age_hours(active_token):.1f} hours)")
        return active_token['value']
    
    def _get_token_age_hours(self, token: Dict[str, Any]) -> float:
        """Get token age in hours for logging purposes"""
        if not token.get('active_from'):
            return 0.0
        
        try:
            token_time = datetime.datetime.fromisoformat(token['active_from'])
            age = datetime.datetime.now() - token_time
            return age.total_seconds() / 3600
        except (ValueError, TypeError):
            return 0.0
    
    def get_active_refresh_token(self) -> Optional[str]:
        """Get the active refresh token value"""
        active_tokens = [token for token in self.tokens if token['active']]
        
        if not active_tokens:
            return None
        
        # Get the most recent active token (highest ID)
        active_token = max(active_tokens, key=lambda x: x['id'])
        return active_token.get('refresh_token')
    
    def increment_token_usage(self):
        """Increment usage for the active token"""
        active_tokens = [token for token in self.tokens if token['active']]
        
        if not active_tokens:
            return
        
        # Get the most recent active token (highest ID)
        active_token = max(active_tokens, key=lambda x: x['id'])
        
        # Update usage and last_used (only on successful API calls)
        active_token['usage'] += 1
        active_token['last_used'] = self._get_current_timestamp()
        
        self._save_tokens()
    
    def increment_token_usage_on_success(self):
        """Increment usage and update last_used for the active token (only on success)"""
        active_tokens = [token for token in self.tokens if token['active']]
        
        if not active_tokens:
            return
        
        # Get the most recent active token (highest ID)
        active_token = max(active_tokens, key=lambda x: x['id'])
        
        # Update usage and last_used (only on successful API calls)
        active_token['usage'] += 1
        active_token['last_used'] = self._get_current_timestamp()
        
        self._save_tokens()
    
    def increment_token_usage_on_failure(self):
        """Increment usage but DON'T update last_used for the active token (only on failure)"""
        active_tokens = [token for token in self.tokens if token['active']]
        
        if not active_tokens:
            return
        
        # Get the most recent active token (highest ID)
        active_token = max(active_tokens, key=lambda x: x['id'])
        
        # Update usage but NOT last_used (failed API calls)
        active_token['usage'] += 1
        
        self._save_tokens()
    
    def _refresh_token(self) -> bool:
        """Attempt to refresh the access token using the refresh token"""
        logger.info("Attempting to refresh access token...")
        
        refresh_token = self.get_active_refresh_token()
        if not refresh_token:
            logger.error("No refresh token available for active token.")
            return False
        
        client_id = 'Atlas_App'
        token_url = f'{self.auth_base_url}/connect/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'scope': 'openid profile email offline_access'  # Optional, but maintains original scopes
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        try:
            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                return False
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL connection failed during token refresh: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed during token refresh: {e}")
            return False
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout during token refresh: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            return False
        
        token_response = response.json()
        new_access_token = token_response.get('access_token')
        new_refresh_token = token_response.get('refresh_token')  # May be rotated or the same
        
        logger.info(f"Token refresh response status: {response.status_code}")
        logger.info(f"New access token length: {len(new_access_token) if new_access_token else 'None'}")
        logger.info(f"New refresh token length: {len(new_refresh_token) if new_refresh_token else 'None'}")
        
        if not new_access_token:
            logger.error("No new access token received during refresh.")
            return False
        
        # Update the existing token (don't create a new one)
        if self.update_existing_token(new_access_token, new_refresh_token):
            logger.info("Access token refreshed successfully.")
            return True
        else:
            logger.error("Failed to update existing token.")
            return False
    
    def api_request_with_token_refresh(self, request_func: Callable, *args, **kwargs) -> Any:
        """
        Wrapper function that handles API requests with automatic token refresh on 401 errors.
        
        Args:
            request_func: The function that makes the actual API request
            *args, **kwargs: Arguments to pass to the request function
        
        Returns:
            The response from the API request
        
        Raises:
            requests.exceptions.HTTPError: If the request fails after token refresh
        """
        # First attempt with current token (don't increment usage yet)
        current_token = self.get_active_token_value()
        logger.info(f"Using token for API call, length: {len(current_token) if current_token else 'None'}")
        
        try:
            result = request_func(*args, **kwargs)
            # If successful, increment usage and update last_used
            self.increment_token_usage_on_success()
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, increment usage but don't update last_used
                self.increment_token_usage_on_failure()
                
                # First, try to refresh using refresh token
                if self._refresh_token():
                    # Retry with refreshed token
                    try:
                        result = request_func(*args, **kwargs)
                        # If successful, increment usage and update last_used
                        self.increment_token_usage_on_success()
                        return result
                    except requests.exceptions.HTTPError as retry_e:
                        # Retry failed, increment failure
                        self.increment_token_usage_on_failure()
                        raise retry_e
                
                # Refresh failed, fall back to generating new token via browser
                logger.warning("Refresh token failed, generating new token via browser...")
                new_tokens = self._generate_new_token()
                if new_tokens:
                    # Retry with new token
                    try:
                        result = request_func(*args, **kwargs)
                        # If successful, increment usage and update last_used
                        self.increment_token_usage_on_success()
                        return result
                    except requests.exceptions.HTTPError as retry_e:
                        # Retry failed, increment failure
                        self.increment_token_usage_on_failure()
                        raise retry_e
                else:
                    # Failed to generate new token
                    raise e
            else:
                # Other HTTP error, increment usage but don't update last_used
                self.increment_token_usage_on_failure()
                raise
    
    def deactivate_token(self, token_id: int) -> bool:
        """Deactivate a specific token"""
        for token in self.tokens:
            if token['id'] == token_id:
                token['active'] = False
                self._save_tokens()
                return True
        return False
    
    def list_tokens(self) -> list:
        """List all tokens with their metadata"""
        return self.tokens.copy()
    
    def get_token_by_id(self, token_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific token by ID"""
        for token in self.tokens:
            if token['id'] == token_id:
                return token.copy()
        return None
