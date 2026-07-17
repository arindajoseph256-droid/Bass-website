from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send a chat message and get a response."""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass

    @abstractmethod
    def generate_questions(self, topic: str, count: int = 5, question_type: str = "multiple_choice") -> List[Dict]:
        """Generate practice questions."""
        pass

    @abstractmethod
    def explain_topic(self, topic: str, context: str = "") -> str:
        """Explain a topic in detail."""
        pass

    @abstractmethod
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Summarize text."""
        pass

    @abstractmethod
    def generate_flashcards(self, text: str, count: int = 10) -> List[Dict]:
        """Generate flashcards from text."""
        pass

    @abstractmethod
    def check_grammar(self, text: str) -> Dict:
        """Check grammar and provide corrections."""
        pass

    @abstractmethod
    def generate_study_plan(self, topic: str, duration_days: int = 7) -> Dict:
        """Generate a study plan."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI implementation of AI provider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.client = None

    def _get_client(self):
        if self.client is None:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
        return self.client

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )
        return response.choices[0].message.content

    def generate_text(self, prompt: str, **kwargs) -> str:
        return self.chat([
            {"role": "system", "content": "You are a helpful AI tutor."},
            {"role": "user", "content": prompt},
        ], **kwargs)

    def generate_questions(self, topic: str, count: int = 5, question_type: str = "multiple_choice") -> List[Dict]:
        prompt = f"""Generate {count} {question_type.replace('_', ' ')} questions about {topic}.
Format the response as a JSON array with this structure:
[
  {{
    "question": "Question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Explanation of the answer"
  }}
]

Return ONLY the JSON array, no other text."""

        response = self.chat([
            {"role": "system", "content": "You are an educational AI that generates quiz questions."},
            {"role": "user", "content": prompt},
        ])

        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []

    def explain_topic(self, topic: str, context: str = "") -> str:
        prompt = f"""Explain the topic '{topic}' in detail.
{'Context: ' + context if context else ''}

Provide a comprehensive explanation suitable for a student learning this topic."""
        return self.generate_text(prompt)

    def summarize_text(self, text: str, max_length: int = 200) -> str:
        prompt = f"""Summarize the following text in no more than {max_length} words:

{text}"""
        return self.generate_text(prompt)

    def generate_flashcards(self, text: str, count: int = 10) -> List[Dict]:
        prompt = f"""Generate {count} flashcards from the following content.
Format as JSON:
[
  {{
    "front": "Question or term",
    "back": "Answer or definition"
  }}
]

Content:
{text}"""

        response = self.chat([
            {"role": "system", "content": "You are an educational AI that creates flashcards."},
            {"role": "user", "content": prompt},
        ])

        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []

    def check_grammar(self, text: str) -> Dict:
        prompt = f"""Check the grammar of the following text and provide corrections:
'{text}'

Format the response as JSON:
{{
  "original": "original text",
  "corrected": "corrected text",
  "corrections": [
    {{"error": "the error", "correction": "the fix", "explanation": "why it's wrong"}}
  ],
  "is_correct": true/false
}}"""

        response = self.chat([
            {"role": "system", "content": "You are an expert grammar checker."},
            {"role": "user", "content": prompt},
        ])

        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"original": text, "corrected": text, "corrections": [], "is_correct": True}

    def generate_study_plan(self, topic: str, duration_days: int = 7) -> Dict:
        prompt = f"""Create a {duration_days}-day study plan for learning '{topic}'.
Format as JSON:
{{
  "topic": "topic name",
  "duration_days": {duration_days},
  "daily_plan": [
    {{
      "day": 1,
      "title": "Day title",
      "topics": ["topic1", "topic2"],
      "activities": ["activity1", "activity2"],
      "estimated_time": "2 hours"
    }}
  ]
}}"""

        response = self.chat([
            {"role": "system", "content": "You are an educational AI that creates study plans."},
            {"role": "user", "content": prompt},
        ])

        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"topic": topic, "duration_days": duration_days, "daily_plan": []}


class AnthropicProvider(AIProvider):
    """Anthropic Claude implementation of AI provider."""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)
        
        response = client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            messages=messages,
        )
        return response.content[0].text

    def generate_text(self, prompt: str, **kwargs) -> str:
        return self.chat([
            {"role": "user", "content": prompt},
        ], **kwargs)

    def generate_questions(self, topic: str, count: int = 5, question_type: str = "multiple_choice") -> List[Dict]:
        prompt = f"""Generate {count} {question_type.replace('_', ' ')} questions about {topic}.
Return as JSON array with question, options, correct_answer, and explanation."""
        return self._parse_json_response(self.generate_text(prompt))

    def explain_topic(self, topic: str, context: str = "") -> str:
        prompt = f"Explain '{topic}' in detail.{' Context: ' + context if context else ''}"
        return self.generate_text(prompt)

    def summarize_text(self, text: str, max_length: int = 200) -> str:
        prompt = f"Summarize in {max_length} words: {text}"
        return self.generate_text(prompt)

    def generate_flashcards(self, text: str, count: int = 10) -> List[Dict]:
        prompt = f"Generate {count} flashcards from: {text}. Return as JSON with front/back."
        return self._parse_json_response(self.generate_text(prompt))

    def check_grammar(self, text: str) -> Dict:
        prompt = f"Grammar check: '{text}'. Return JSON with original, corrected, corrections."
        return self._parse_json_response(self.generate_text(prompt), {"original": text, "corrected": text, "corrections": [], "is_correct": True})

    def generate_study_plan(self, topic: str, duration_days: int = 7) -> Dict:
        prompt = f"{duration_days}-day study plan for '{topic}'. Return JSON with daily_plan."
        return self._parse_json_response(self.generate_text(prompt), {"topic": topic, "duration_days": duration_days, "daily_plan": []})

    def _parse_json_response(self, response: str, default=None):
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return default or []


def get_ai_provider() -> AIProvider:
    """Factory function to get the configured AI provider."""
    from django.conf import settings
    
    provider = getattr(settings, "AI_PROVIDER", "openai")
    model = getattr(settings, "AI_MODEL", "gpt-4")
    
    if provider == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        return OpenAIProvider(api_key, model)
    
    elif provider == "anthropic":
        api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")
        return AnthropicProvider(api_key, model)
    
    else:
        raise ValueError(f"Unknown AI provider: {provider}")
