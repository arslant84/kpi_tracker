from google import genai
from google.genai import types
from google.genai import errors as genai_errors
import json
import re
import logging
import time
import hashlib
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


class GeminiService:
    CACHE_TTL = 60 * 60 * 24
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    DEFAULT_MODEL = "gemini-2.0-flash"

    def _get_cache_key(self, prompt, model):
        key = f"{prompt}:{model}"
        return f"gemini_cache:{hashlib.md5(key.encode()).hexdigest()}"

    @staticmethod
    def _is_daily_quota_exhausted(e):
        return 'PerDay' in str(e)

    def _handle_api_error(self, e, operation):
        error_msg = str(e)
        if isinstance(e, genai_errors.ClientError) and '429' in error_msg:
            if self._is_daily_quota_exhausted(e):
                logger.error(f"Gemini daily quota exhausted during {operation}.")
                return "Daily API quota exhausted. Please enable billing at aistudio.google.com or try again tomorrow."
            logger.warning(f"Gemini rate limit during {operation}: {error_msg}")
            return "Rate limit exceeded. Please try again in a few moments."
        elif isinstance(e, genai_errors.ClientError) and any(c in error_msg for c in ('401', '403')):
            logger.error(f"Gemini auth error during {operation}: {error_msg}")
            return "API authentication error. Please check your Gemini API key."
        else:
            logger.error(f"Gemini API error during {operation}: {error_msg}")
            return "An error occurred while processing your request. Please try again later."

    def chat_completion(self, messages, model=None, temperature=0.7, use_cache=True):
        model = model or self.DEFAULT_MODEL
        prompt_str = json.dumps(messages)

        if use_cache:
            cache_key = self._get_cache_key(prompt_str, model)
            cached = cache.get(cache_key)
            if cached:
                logger.info("Using cached Gemini response.")
                return cached

        system_msg = next((m['content'] for m in messages if m['role'] == 'system'), None)
        user_msg = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), '')

        config = types.GenerateContentConfig(
            system_instruction=system_msg,
            temperature=temperature,
        )

        client = _get_client()

        for attempt in range(self.MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=user_msg,
                    config=config,
                )
                text = response.text.strip()

                if use_cache:
                    cache.set(cache_key, text, self.CACHE_TTL)

                return text

            except genai_errors.ClientError as e:
                if '429' in str(e):
                    # Daily quota is permanent for today — don't retry
                    if self._is_daily_quota_exhausted(e):
                        return self._handle_api_error(e, "chat completion")
                    logger.warning(f"Gemini rate limit, attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY * (2 ** attempt))
                        continue
                return self._handle_api_error(e, "chat completion")
            except Exception as e:
                return self._handle_api_error(e, "chat completion")

    def _extract_json_from_response(self, response_text):
        if not response_text:
            return None
        # Strip markdown code fences Gemini sometimes wraps around JSON
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', response_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r'\[.*\]|\{.*\}', cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            logger.error(f"Failed to extract JSON from Gemini response: {response_text[:200]}")
            return None

    def generate_kpi_insight(self, task_context):
        days_info = (
            f"{task_context['days_remaining']} days remaining"
            if task_context['days_remaining'] is not None
            else "no deadline set"
        )
        overdue = task_context['days_remaining'] is not None and task_context['days_remaining'] < 0

        prompt = f"""You are a KPI performance advisor. Analyze this KPI task and provide clear, specific insights.

Goal: {task_context['goal_name']} (Weight: {task_context['goal_weight']}%)
Task Description: {task_context['description']}
Unit of Measurement: {task_context['unit_of_measurement'] or 'Not specified'}
Base Target: {task_context['base_target'] or 'Not specified'}
Stretch Target: {task_context['stretch_target'] or 'Not specified'}
Deadline: {task_context['base_deadline'] or 'Not set'} ({days_info}{', OVERDUE' if overdue else ''})
Current Completion: {task_context['completion_level']}%
Current Status: {task_context['status']}
Progress Notes: {task_context['notes'] or 'None provided'}

Respond ONLY with valid JSON in this exact structure:
{{
    "risk_level": "green",
    "summary": "2-3 sentence assessment of the current trajectory and what it means.",
    "advice": "Specific, actionable advice tailored to the exact context of this KPI.",
    "recommended_actions": ["Concrete action 1", "Concrete action 2", "Concrete action 3"],
    "predicted_outcome": "Brief prediction of whether base/stretch target will be met based on current pace."
}}

risk_level must be one of: "green" (on track), "amber" (at risk), "red" (behind / critical)."""

        messages = [
            {"role": "system", "content": "You are a KPI performance advisor. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ]
        response = self.chat_completion(messages, use_cache=False)
        data = self._extract_json_from_response(response)
        if data and 'risk_level' in data:
            return data
        return None

    def analyze_portfolio(self, portfolio_data):
        goals_text = []
        for goal in portfolio_data['goals']:
            tasks_lines = []
            for t in goal['tasks']:
                dl = f", due {t['base_deadline']}" if t['base_deadline'] else ""
                tasks_lines.append(
                    f"    • {t['description'][:90]}: {t['completion_level']}% ({t['status']}{dl})"
                )
            goals_text.append(
                f"Goal: {goal['name']} | Weight: {goal['weight']}% | Overall: {goal['overall_completion']}%\n"
                + "\n".join(tasks_lines)
            )

        breakdown = portfolio_data['status_breakdown']
        prompt = f"""You are a senior KPI portfolio analyst. Analyze this complete KPI portfolio.

Portfolio Overview:
- Total Goals: {portfolio_data['total_goals']} | Total Tasks: {portfolio_data['total_tasks']}
- Overall Avg Completion: {portfolio_data['overall_completion']}%
- Status: {breakdown.get('completed', 0)} completed, {breakdown.get('on_track', 0)} on track, {breakdown.get('behind', 0)} behind, {breakdown.get('ahead', 0)} ahead, {breakdown.get('not_started', 0)} not started

Goals Detail:
{chr(10).join(goals_text)}

Respond ONLY with valid JSON in this exact structure:
{{
    "portfolio_health": "green",
    "health_score": 72,
    "executive_summary": "3-4 sentence strategic overview of the portfolio's current state and trajectory.",
    "key_risks": ["Specific risk 1 citing the goal/task", "Specific risk 2", "Specific risk 3"],
    "critical_goals": ["Goal name that is most at risk"],
    "weighted_performance": "One paragraph assessing performance relative to goal weights — which high-weight goals are lagging and what that means.",
    "strategic_recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
    "predicted_year_end": "Prediction of overall portfolio outcome by end of cycle."
}}

portfolio_health must be one of: "green", "amber", "red". health_score is 0-100."""

        messages = [
            {"role": "system", "content": "You are a senior KPI portfolio analyst. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ]
        response = self.chat_completion(messages, use_cache=False)
        data = self._extract_json_from_response(response)
        if data and 'portfolio_health' in data:
            return data
        return None
