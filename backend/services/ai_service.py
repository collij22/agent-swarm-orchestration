import os
import logging
from typing import Dict, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

class AIService:
    def __init__(self):
        # Secure API key retrieval
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.logger = logging.getLogger(__name__)
        self.model = "gpt-3.5-turbo"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def categorize_task(self, task_description: str) -> Optional[str]:
        """
        AI-powered task categorization with robust error handling
        
        Args:
            task_description (str): Detailed task description
        
        Returns:
            Optional[str]: Suggested task category
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a task categorization expert. Categorize the following task into one of these categories: Work, Personal, Health, Learning, Finance, Other."},
                    {"role": "user", "content": task_description}
                ],
                max_tokens=20
            )
            category = response.choices[0].message.content.strip()
            return category
        except Exception as e:
            self.logger.error(f"AI Categorization Error: {str(e)}")
            return "Other"  # Fallback category
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def score_task_priority(self, task_description: str) -> int:
        """
        AI-powered task priority scoring with robust error handling
        
        Args:
            task_description (str): Detailed task description
        
        Returns:
            int: Priority score (1-5)
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a task priority expert. Score the following task's priority from 1-5, where 1 is low priority and 5 is critical."},
                    {"role": "user", "content": task_description}
                ],
                max_tokens=10
            )
            priority_str = response.choices[0].message.content.strip()
            priority = max(1, min(5, int(priority_str)))
            return priority
        except Exception as e:
            self.logger.error(f"AI Priority Scoring Error: {str(e)}")
            return 3  # Default medium priority
    
    def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key configuration
        
        Returns:
            bool: Whether API key is valid and working
        """
        try:
            openai.Model.list()
            return True
        except Exception:
            return False

# Example usage
if __name__ == "__main__":
    ai_service = AIService()
    task_desc = "Prepare quarterly financial report for the management meeting"
    print(f"Category: {ai_service.categorize_task(task_desc)}")
    print(f"Priority: {ai_service.score_task_priority(task_desc)}")