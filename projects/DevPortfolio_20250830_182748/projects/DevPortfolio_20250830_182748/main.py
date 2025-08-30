import asyncio
import logging
from typing import Dict, Any
import yaml

from src.services.integrations import get_integration_service

class DevPortfolioApp:
    def __init__(self, config_path: str = 'config/integrations.yml'):
        self.logger = logging.getLogger('devportfolio')
        self.config = self._load_config(config_path)
        self.integration_service = get_integration_service(self.config)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Config loading failed: {e}")
            raise

    async def initialize_integrations(self):
        """Initialize and validate external service integrations"""
        try:
            # GitHub integration test
            github_test = await self.integration_service.fetch_github_repos('sample_username')
            self.logger.info(f"GitHub integration successful. Repos found: {len(github_test)}")

            # OpenAI integration test
            openai_test = await self.integration_service.generate_openai_content("Test content generation")
            self.logger.info(f"OpenAI integration test successful. Generated content length: {len(openai_test)}")

        except Exception as e:
            self.logger.error(f"Integration initialization failed: {e}")
            raise

    async def run(self):
        """Main application run method"""
        logging.basicConfig(level=logging.INFO)
        await self.initialize_integrations()

async def main():
    app = DevPortfolioApp()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())