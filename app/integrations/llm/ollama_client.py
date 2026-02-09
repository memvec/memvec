from __future__ import annotations

import json
import os
import logging
from typing import Any

import requests

from app.integrations.llm.base import LLMClient


logger = logging.getLogger(__name__)


class LLMJSONError(Exception):
    """I raise this when the model refuses to give me usable JSON."""


class OllamaClient(LLMClient):
    """
    I keep this client tiny: JSON-in, JSON-out, no surprises.
    """

    def __init__(self) -> None:
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'qwen2.5')

        logger.debug(
            'Initialized OllamaClient',
            extra={
                'base_url': self.base_url,
                'model': self.model,
            },
        )

    def generate_json(self, system_prompt: str, user_prompt: str, timeout_s: int = 30) -> Any:
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'stream': False,
            'options': {
                'temperature': 0.0,
            },
        }

        logger.debug(
            'Sending request to Ollama',
            extra={
                'url': f'{self.base_url}/api/chat',
                'timeout_s': timeout_s,
            },
        )

        try:
            resp = requests.post(
                f'{self.base_url}/api/chat',
                json=payload,
                timeout=timeout_s,
            )
            
            resp.raise_for_status()
        except Exception:
            logger.exception('HTTP request to Ollama failed')
            raise

        try:
            resp_json = resp.json()
        except Exception:
            logger.exception('Failed to decode Ollama response as JSON')
            raise

        content = resp_json.get('message', {}).get('content', '').strip()
        logger.debug('Received LLM response')
        #logger.debug('LLM content (first 1000 chars): %s', content[:1000])

        # First attempt: strict JSON
        try:
            return json.loads(content)
        except Exception:
            logger.debug(
                'Strict JSON parsing failed, attempting snippet recovery',
                exc_info=True,
            )

        # Fallback: extract JSON snippet
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            snippet = content[start : end + 1]
            try:
                return json.loads(snippet)
            except Exception as e:
                logger.exception(
                    'Failed parsing JSON snippet from LLM output',
                    extra={
                        'snippet_preview': snippet[:500],
                    },
                )
                raise LLMJSONError(f'Failed parsing JSON snippet: {e}') from e

        logger.error(
            'LLM output did not contain valid JSON',
            extra={
                'content_preview': content[:500],
            },
        )
        raise LLMJSONError('LLM output was not valid JSON.')
