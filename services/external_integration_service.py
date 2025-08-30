import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

class ExternalIntegrationService:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize integration service with configuration
        
        :param config: External services configuration
        """
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def request(
        self, 
        service: str, 
        method: str, 
        endpoint: str, 
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make a generic request to external services with advanced error handling
        
        :param service: Service name (github, openai, etc.)
        :param method: HTTP method
        :param endpoint: API endpoint
        :param headers: Request headers
        :param params: Query parameters
        :param data: Request payload
        :return: API response
        """
        try:
            service_config = self._config.get(service, {})
            base_url = service_config.get('base_url')
            
            if not base_url:
                raise ValueError(f"No base URL configured for {service}")

            full_url = f"{base_url}{endpoint}"
            default_headers = {
                'Accept': 'application/json',
                'User-Agent': 'DevPortfolio/1.0'
            }
            headers = {**default_headers, **(headers or {})}

            async with self._session.request(
                method, 
                full_url, 
                headers=headers, 
                params=params, 
                json=data
            ) as response:
                # Advanced error handling
                if response.status >= 400:
                    error_text = await response.text()
                    self._logger.error(
                        f"API Error: {service} - {response.status} - {error_text}"
                    )
                    response.raise_for_status()

                return await response.json()

        except aiohttp.ClientError as e:
            self._logger.error(f"Client error in {service} integration: {e}")
            raise
        except Exception as e:
            self._logger.exception(f"Unexpected error in {service} integration")
            raise

    async def get_github_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Retrieve GitHub user profile
        
        :param username: GitHub username
        :return: User profile data
        """
        return await self.request(
            service='github',
            method='GET', 
            endpoint=f'/users/{username}'
        )

    async def generate_ai_content(self, prompt: str) -> str:
        """
        Generate content using OpenAI
        
        :param prompt: Content generation prompt
        :return: Generated content
        """
        response = await self.request(
            service='openai',
            method='POST',
            endpoint='/v1/chat/completions',
            data={
                'model': 'gpt-4-turbo',
                'messages': [{'role': 'user', 'content': prompt}]
            }
        )
        return response['choices'][0]['message']['content']

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)