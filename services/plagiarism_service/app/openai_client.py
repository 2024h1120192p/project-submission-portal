"""OpenAI client for AI-generated content detection.

This module provides integration with OpenAI's API to detect
AI-generated content in research paper submissions.
"""
import json
from typing import Optional
from config.logging import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class OpenAIClient:
    """Client for OpenAI API integration for AI content detection."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If not provided, uses settings.
            model: Model to use. If not provided, uses settings.
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.enabled = bool(self.api_key) and settings.OPENAI_ENABLED
        self._client = None
        
        if self.enabled:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.warning("OpenAI package not installed - AI detection disabled")
                self.enabled = False
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False
    
    async def detect_ai_content(self, text: str) -> dict:
        """Analyze text for AI-generated content indicators.
        
        Uses OpenAI's API to analyze text patterns that might indicate
        AI-generated content.
        
        Args:
            text: The text content to analyze
            
        Returns:
            Dictionary containing:
                - ai_probability: Float between 0 and 1
                - confidence: Confidence level of the detection
                - indicators: List of detected AI indicators
                - analysis: Brief analysis text
        """
        if not self.enabled or not self._client:
            logger.debug("OpenAI detection disabled, returning default values")
            return {
                "ai_probability": 0.0,
                "confidence": "low",
                "indicators": [],
                "analysis": "OpenAI detection not enabled",
                "openai_used": False
            }
        
        # Truncate text if too long (to manage API costs)
        max_chars = 4000
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        prompt = f"""Analyze the following text for indicators of AI-generated content.
Consider these factors:
1. Repetitive patterns or structures
2. Unusually consistent tone throughout
3. Generic or templated phrasing
4. Lack of personal voice or unique insights
5. Perfect grammar with no natural variations

Text to analyze:
---
{truncated_text}
---

Respond with a JSON object containing:
- ai_probability: a number between 0 and 1 indicating likelihood of AI generation
- confidence: "low", "medium", or "high"
- indicators: list of specific indicators found
- analysis: brief explanation of findings

Respond ONLY with valid JSON, no additional text."""

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI content detection expert. Analyze text for signs of AI generation and respond with structured JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                result = json.loads(content)
                result["openai_used"] = True
                return result
            except json.JSONDecodeError:
                # If response isn't valid JSON, return a default structure
                logger.warning("OpenAI response was not valid JSON")
                return {
                    "ai_probability": 0.5,
                    "confidence": "low",
                    "indicators": ["Analysis parsing failed"],
                    "analysis": content[:200],
                    "openai_used": True
                }
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "ai_probability": 0.0,
                "confidence": "low",
                "indicators": [],
                "analysis": f"OpenAI analysis failed: {str(e)}",
                "openai_used": False
            }


# Global client instance
_openai_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """Get or create the global OpenAI client instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
