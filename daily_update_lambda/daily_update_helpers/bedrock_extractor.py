import json
import logging

import boto3

from daily_update_helpers.daily_update_constants import (
    BEDROCK_MODEL_ID,
    BEDROCK_REGION,
)

logger = logging.getLogger(__name__)


class BedrockExtractor:
    """Thin wrapper around Bedrock's Claude models for text extraction tasks.

    Site markup with obfuscated, frequently-changing class names is brittle to
    parse with hand-tuned selectors, so scrapers can hand a rough text dump to
    Claude and get back clean structured data. Uses Haiku by default (cheap and
    fast, sufficient for extraction). Mirrors the InvokeModel pattern used by
    the shelf-aware backend.
    """

    def __init__(self, model_id: str = BEDROCK_MODEL_ID, region: str = BEDROCK_REGION):
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        """Send a single text prompt and return the model's text response."""
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "user", "content": [{"type": "text", "text": prompt}]}
                    ],
                }
            ),
        )
        payload = json.loads(response["body"].read())
        text = next(
            (c.get("text", "") for c in payload.get("content", []) if c.get("type") == "text"),
            "",
        )
        usage = payload.get("usage", {})
        logger.info(
            "Bedrock %s: in=%s out=%s tokens",
            self.model_id,
            usage.get("input_tokens"),
            usage.get("output_tokens"),
        )
        return text

    def extract_json(self, prompt: str, max_tokens: int = 2048):
        """Run a prompt expected to return JSON; parse and return it (or None)."""
        text = self.complete(prompt, max_tokens=max_tokens)
        return self._parse_json(text)

    @staticmethod
    def _parse_json(text: str):
        """Parse model output as JSON, tolerating ```json fences."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.split("\n")[1:-1]).strip()
        try:
            return json.loads(cleaned)
        except (ValueError, TypeError):
            logger.error("Could not parse Bedrock JSON output: %s", cleaned[:200])
            return None
