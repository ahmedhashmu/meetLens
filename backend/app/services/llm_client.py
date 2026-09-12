"""LLM client for bounded agent analysis."""
import json
import time
import os
from typing import Dict, Any
from app.core.config import settings
from app.models.schemas import AnalysisSignals
from pydantic import ValidationError
import httpx


class LLMClient:
    """Client for LLM API calls with bounded agent design."""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        
        # Validate and fix model name
        valid_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "grok-beta"]
        print(f"Raw LLM_MODEL from settings: '{settings.LLM_MODEL}'")
        if self.model not in valid_models:
            print(f"WARNING: Invalid model '{self.model}', falling back to 'gpt-4o-mini'")
            self.model = "gpt-4o-mini"
        
        print(f"Initializing LLM Client - Provider: {self.provider}, Model: {self.model}")
        
        # Use frontend API proxy to bypass Railway network restrictions
        self.use_frontend_proxy = os.getenv("USE_FRONTEND_LLM_PROXY", "false").lower() == "true"
        # Clean the URL - remove any whitespace, newlines, or non-printable characters
        self.frontend_url = os.getenv("FRONTEND_URL", "").strip().replace('\n', '').replace('\r', '').replace('\t', '')
        
        if self.use_frontend_proxy:
            print(f"Using frontend LLM proxy at: {self.frontend_url}")
            self.http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=10.0),
                follow_redirects=True
            )
        else:
            # Original OpenAI/xAI client setup
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                follow_redirects=True
            )
            
            if self.provider == "openai":
                from openai import OpenAI
                api_key = settings.OPENAI_API_KEY
                if not api_key:
                    print("ERROR: OPENAI_API_KEY is not set!")
                else:
                    # Check for whitespace issues
                    api_key_clean = api_key.strip()
                    if api_key != api_key_clean:
                        print(f"WARNING: OPENAI_API_KEY has whitespace, cleaning...")
                        api_key = api_key_clean
                    print(f"OpenAI API Key loaded: {api_key[:10]}...{api_key[-4:]}")
                    print(f"API Key length: {len(api_key)}")
                
                # Explicit base URL
                base_url = "https://api.openai.com/v1"
                print(f"Using OpenAI base URL: {base_url}")
                
                # Try using a custom base URL that might not be blocked
                self.client = OpenAI(
                    api_key=api_key, 
                    http_client=http_client,
                    base_url=base_url
                )
                print(f"OpenAI client initialized successfully")
            elif self.provider == "xai":
                from openai import OpenAI
                api_key = settings.XAI_API_KEY
                if not api_key:
                    print("ERROR: XAI_API_KEY is not set!")
                else:
                    print(f"xAI API Key loaded: {api_key[:10]}...{api_key[-4:]}")
                # xAI uses OpenAI-compatible API
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.x.ai/v1",
                    http_client=http_client
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def extract_signals(self, transcript: str, max_retries: int = 3) -> AnalysisSignals:
        """
        Extract structured signals from transcript using bounded agent.
        
        Args:
            transcript: Meeting transcript text
            max_retries: Maximum number of retry attempts
            
        Returns:
            Validated structured signals
            
        Raises:
            Exception: If all retries fail
        """
        # Use frontend proxy if enabled
        if self.use_frontend_proxy:
            return self._extract_via_frontend_proxy(transcript, max_retries)
        
        # Original OpenAI/xAI logic
        prompt = self._build_prompt(transcript)
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting LLM call (attempt {attempt + 1}/{max_retries})...")
                print(f"Provider: {self.provider}, Model: {self.model}")
                
                # Call LLM API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a meeting analysis assistant. You extract structured information from meeting transcripts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    max_tokens=1000
                )
                
                # Extract response content
                content = response.choices[0].message.content
                print(f"LLM response received successfully")
                
                # Parse JSON
                data = json.loads(content)
                
                # Validate against schema
                signals = AnalysisSignals(**data)
                
                print(f"✓ LLM analysis completed successfully")
                return signals
                
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"Validation error on attempt {attempt + 1}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"All retries exhausted, falling back to demo mode")
                    # Fallback to demo mode
                    return self._generate_demo_analysis(transcript)
            
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                print(f"LLM API error on attempt {attempt + 1}: {error_msg}")
                print(f"Error type: {error_type}")
                
                # Log full exception details for debugging
                import traceback
                print(f"Full traceback:")
                traceback.print_exc()
                
                # Check for specific error attributes
                if hasattr(e, '__cause__'):
                    print(f"Underlying cause: {type(e.__cause__).__name__}: {e.__cause__}")
                if hasattr(e, 'response'):
                    print(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
                
                # Check if it's a connection error and add more wait time
                if "Connection" in error_type or "Timeout" in error_type:
                    wait_time = 2 ** (attempt + 1)  # Longer backoff for connection errors
                    print(f"Connection issue detected, waiting {wait_time}s before retry...")
                else:
                    wait_time = 2 ** attempt
                
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"All retries exhausted, falling back to demo mode")
                    print(f"Final error was: {error_msg}")
                    # Fallback to demo mode
                    return self._generate_demo_analysis(transcript)
    
    def _extract_via_frontend_proxy(self, transcript: str, max_retries: int = 3) -> AnalysisSignals:
        """Extract signals by calling frontend LLM proxy API."""
        for attempt in range(max_retries):
            try:
                print(f"Calling frontend LLM proxy (attempt {attempt + 1}/{max_retries})...")
                
                response = self.http_client.post(
                    f"{self.frontend_url}/api/llm/analyze",
                    json={"transcript": transcript},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    signals = AnalysisSignals(**data)
                    print(f"✓ LLM analysis completed via frontend proxy")
                    return signals
                else:
                    print(f"Frontend proxy error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"Frontend proxy error on attempt {attempt + 1}: {str(e)}")
                
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
        
        print(f"All frontend proxy attempts failed, falling back to demo mode")
        return self._generate_demo_analysis(transcript)
    
    def _generate_demo_analysis(self, transcript: str) -> AnalysisSignals:
        """Generate demo analysis when LLM is unavailable."""
        # Simple keyword-based analysis for demo
        transcript_lower = transcript.lower()
        
        # Determine sentiment
        positive_words = ['great', 'excellent', 'interested', 'excited', 'good', 'perfect', 'happy', 'love', 'amazing', 'wonderful', 'fantastic', 'positive', 'agree', 'yes', 'definitely', 'absolutely']
        negative_words = ['concern', 'worried', 'problem', 'issue', 'difficult', 'expensive', 'no', 'not', 'cannot', 'won\'t', 'disappointed', 'frustrated', 'angry', 'bad', 'poor']
        
        positive_count = sum(1 for word in positive_words if word in transcript_lower)
        negative_count = sum(1 for word in negative_words if word in transcript_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Extract topics (improved - filter out names and common words)
        words = transcript_lower.split()
        # Common words to exclude
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
            'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'them', 'their', 'our', 'your',
            'said', 'says', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'from', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'now'
        }
        
        # Filter out names (words ending with :) and common words
        word_freq = {}
        for word in words:
            # Skip names (like "sarah:", "john:")
            if word.endswith(':'):
                continue
            # Clean punctuation
            clean_word = word.strip('.,!?;:"\'')
            if len(clean_word) > 3 and clean_word not in common_words:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # Get top topics
        topics = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:5]
        if not topics:
            topics = ['general discussion']
        
        # Extract objections (look for concern/problem patterns)
        objections = []
        sentences = transcript.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in ['concern', 'worried', 'problem', 'issue', 'but', 'however']):
                clean_sentence = sentence.strip()
                if clean_sentence and len(clean_sentence) > 10:
                    objections.append(clean_sentence[:100])
        
        if not objections:
            objections = ['No major objections identified']
        
        # Extract commitments (look for action/commitment patterns)
        commitments = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in ['will', 'commit', 'promise', 'agree', 'next step', 'follow up', 'schedule']):
                clean_sentence = sentence.strip()
                if clean_sentence and len(clean_sentence) > 10:
                    commitments.append(clean_sentence[:100])
        
        if not commitments:
            commitments = ['No specific commitments identified']
        
        # Determine outcome
        if 'closed' in transcript_lower or 'deal' in transcript_lower or 'signed' in transcript_lower:
            outcome = 'closed'
        elif 'follow' in transcript_lower or 'next' in transcript_lower or 'schedule' in transcript_lower:
            outcome = 'follow_up'
        elif 'not interested' in transcript_lower or 'no interest' in transcript_lower or 'pass' in transcript_lower:
            outcome = 'no_interest'
        else:
            outcome = 'unknown'
        
        # Generate summary
        summary = f"Meeting analysis: {sentiment.capitalize()} sentiment detected. "
        summary += f"Key topics discussed include {', '.join(topics[:3])}. "
        if outcome != 'unknown':
            summary += f"Outcome: {outcome.replace('_', ' ')}. "
        summary += "(Note: Generated using fallback analysis - LLM API unavailable)"
        
        return AnalysisSignals(
            sentiment=sentiment,
            topics=topics,
            objections=objections[:5],  # Limit to 5
            commitments=commitments[:5],  # Limit to 5
            outcome=outcome,
            summary=summary
        )
    
    def _build_prompt(self, transcript: str) -> str:
        """Build structured prompt with JSON schema."""
        return f"""Analyze the following meeting transcript and extract structured information.

You must respond with valid JSON matching this exact schema:
{{
  "sentiment": "positive" | "neutral" | "negative",
  "topics": ["topic1", "topic2", ...],
  "objections": ["objection1", ...],
  "commitments": ["commitment1", ...],
  "outcome": "closed" | "follow_up" | "no_interest" | "unknown",
  "summary": "brief summary"
}}

Rules:
- sentiment: Overall tone of the meeting
- topics: Main subjects discussed (3-5 items)
- objections: Concerns or hesitations raised (0-5 items)
- commitments: Promises or next steps agreed upon (0-5 items)
- outcome: Meeting result classification
- summary: 2-3 sentence summary

Transcript:
{transcript}

Respond only with valid JSON, no additional text."""