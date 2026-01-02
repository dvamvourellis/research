"""
Trend Analyzer Module
Extracts key trends and data points from fetched AI content.
"""

import json
import os
from typing import Dict, List, Optional
from anthropic import Anthropic


class TrendAnalyzer:
    """Analyzes AI trends from fetched content using Claude."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the analyzer.

        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = Anthropic(api_key=self.api_key)

    def analyze_content(self, content_data: Dict[str, Dict[str, str]]) -> Dict[str, any]:
        """
        Analyze fetched content to extract key trends and data points.

        Args:
            content_data: Dictionary of fetched content from sources

        Returns:
            Dictionary containing extracted trends, data points, and insights
        """
        # Prepare content summary for analysis
        content_summary = self._prepare_content_for_analysis(content_data)

        analysis_prompt = f"""You are an expert AI industry analyst. Analyze the following content from trusted AI sources and extract:

1. **Key Trends**: Major trends in AI development, infrastructure, and deployment
2. **Data Points**: Specific numerical data (e.g., compute gaps, capacity shortages, market sizes)
3. **Supply Chain Insights**: Bottlenecks, shortages, or opportunities in the AI supply chain
4. **Technology Trends**: Specific technologies, architectures, or approaches gaining traction
5. **Market Dynamics**: Competitive dynamics, market shifts, and business model changes

Content from sources:
{content_summary}

Please provide a structured analysis in the following JSON format:
{{
  "key_trends": [
    {{
      "trend": "trend description",
      "evidence": "supporting evidence from sources",
      "importance": "high|medium|low",
      "time_horizon": "short-term|medium-term|long-term"
    }}
  ],
  "data_points": [
    {{
      "metric": "metric name",
      "value": "numerical value or range",
      "source": "which source mentioned this",
      "context": "context and implications"
    }}
  ],
  "supply_chain_insights": [
    {{
      "area": "area of supply chain",
      "insight": "insight description",
      "opportunity": "investment opportunity description"
    }}
  ],
  "technology_trends": [
    {{
      "technology": "technology name",
      "adoption_stage": "emerging|growing|mature",
      "key_players": ["list of companies"],
      "investment_angle": "how this creates investment opportunities"
    }}
  ]
}}

Focus on trends and data that have clear investment implications. Be specific and cite evidence from the sources."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            # Extract the response text
            response_text = response.content[0].text

            # Try to parse JSON from the response
            analysis_result = self._extract_json_from_response(response_text)

            return analysis_result

        except Exception as e:
            print(f"Error during analysis: {e}")
            return self._get_empty_analysis()

    def _prepare_content_for_analysis(self, content_data: Dict[str, Dict[str, str]]) -> str:
        """
        Prepare content for analysis by concatenating and formatting.

        Args:
            content_data: Raw fetched content

        Returns:
            Formatted string for analysis
        """
        formatted_content = []

        for source_name, data in content_data.items():
            if data.get('content'):
                formatted_content.append(f"\n\n{'='*80}\nSOURCE: {source_name.upper()}")
                formatted_content.append(f"Title: {data.get('title', 'N/A')}")
                formatted_content.append(f"URL: {data.get('url', 'N/A')}")
                formatted_content.append(f"{'='*80}\n")

                # Truncate very long content
                content = data['content']
                if len(content) > 50000:
                    content = content[:50000] + "\n\n[Content truncated...]"

                formatted_content.append(content)

        return '\n'.join(formatted_content)

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """
        Extract JSON from Claude's response, handling markdown code blocks.

        Args:
            response_text: Raw response text

        Returns:
            Parsed JSON dictionary
        """
        # Try to find JSON in code blocks
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            json_str = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            json_str = response_text[start:end].strip()
        else:
            # Try to find JSON object directly
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Attempted to parse: {json_str[:500]}...")
            return self._get_empty_analysis()

    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            "key_trends": [],
            "data_points": [],
            "supply_chain_insights": [],
            "technology_trends": []
        }

    def save_analysis(self, analysis: Dict, filename: str = 'data/trend_analysis.json'):
        """
        Save analysis results to file.

        Args:
            analysis: Analysis results
            filename: Output filename
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"Analysis saved to {filename}")

    def print_summary(self, analysis: Dict):
        """Print a human-readable summary of the analysis."""
        print("\n" + "="*80)
        print("TREND ANALYSIS SUMMARY")
        print("="*80)

        print(f"\n📊 Key Trends ({len(analysis.get('key_trends', []))} found):")
        for i, trend in enumerate(analysis.get('key_trends', [])[:5], 1):
            print(f"\n{i}. {trend.get('trend', 'N/A')}")
            print(f"   Importance: {trend.get('importance', 'N/A')} | "
                  f"Horizon: {trend.get('time_horizon', 'N/A')}")

        print(f"\n📈 Data Points ({len(analysis.get('data_points', []))} found):")
        for i, dp in enumerate(analysis.get('data_points', [])[:5], 1):
            print(f"\n{i}. {dp.get('metric', 'N/A')}: {dp.get('value', 'N/A')}")
            print(f"   Context: {dp.get('context', 'N/A')[:100]}...")

        print(f"\n🔗 Supply Chain Insights ({len(analysis.get('supply_chain_insights', []))} found):")
        for i, insight in enumerate(analysis.get('supply_chain_insights', [])[:5], 1):
            print(f"\n{i}. {insight.get('area', 'N/A')}")
            print(f"   Opportunity: {insight.get('opportunity', 'N/A')[:100]}...")

        print(f"\n💡 Technology Trends ({len(analysis.get('technology_trends', []))} found):")
        for i, tech in enumerate(analysis.get('technology_trends', [])[:5], 1):
            print(f"\n{i}. {tech.get('technology', 'N/A')} ({tech.get('adoption_stage', 'N/A')})")
            print(f"   Investment Angle: {tech.get('investment_angle', 'N/A')[:100]}...")


if __name__ == "__main__":
    import sys
    from typing import Optional

    # Load fetched content
    try:
        with open('data/fetched_content.json', 'r', encoding='utf-8') as f:
            content_data = json.load(f)
    except FileNotFoundError:
        print("Error: data/fetched_content.json not found. Run fetcher.py first.")
        sys.exit(1)

    # Analyze
    analyzer = TrendAnalyzer()
    analysis = analyzer.analyze_content(content_data)

    # Save and print
    analyzer.save_analysis(analysis)
    analyzer.print_summary(analysis)
