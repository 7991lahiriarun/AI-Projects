from typing import Optional
import os
import requests

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("MODEL_PROVIDER","anthropic")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    def _call_anthropic(self, prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Client(api_key=self.anthropic_key)
            response = client.completions.create(
                model="claude-2", # user can change
                prompt=anthropic.HUMAN_PROMPT + prompt + anthropic.AI_PROMPT,
                max_tokens_to_sample=512,
            )
            return response.completion
        except Exception as e:
            return f"[anthropic call failed: {e}]"

    def _call_local(self, prompt: str) -> str:
        # Very small local fallback using Hugging Face transformers (causal) if available
        try:
            from transformers import pipeline
            gen = pipeline("text-generation", model="gpt2", device=-1)
            out = gen(prompt, max_new_tokens=256, do_sample=True, temperature=0.7)
            return out[0]["generated_text"]
        except Exception as e:
            return f"[local generation failed: {e}]"

    def generate(self, prompt: str) -> str:
        if self.provider == "anthropic" and self.anthropic_key:
            return self._call_anthropic(prompt)
        else:
            return self._call_local(prompt)
