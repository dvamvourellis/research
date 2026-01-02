"""
Investment Themes Generator
Converts AI trends into actionable investment themes.
"""

import json
import os
from typing import Dict, List, Optional
from anthropic import Anthropic


class InvestmentThemeGenerator:
    """Generates investment themes from trend analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the theme generator.

        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = Anthropic(api_key=self.api_key)

    def generate_themes(self, trend_analysis: Dict) -> Dict[str, any]:
        """
        Generate investment themes from trend analysis.

        Args:
            trend_analysis: Output from TrendAnalyzer

        Returns:
            Dictionary containing investment themes
        """
        # Prepare the analysis summary
        analysis_summary = self._prepare_analysis_summary(trend_analysis)

        themes_prompt = f"""You are an expert investment strategist specializing in AI and technology sectors. Based on the following trend analysis, generate specific investment themes for a 1-2 year investment horizon.

Trend Analysis:
{analysis_summary}

Generate investment themes that are:
1. **Specific and Actionable**: Clear enough to identify relevant stocks
2. **Data-Driven**: Based on the concrete trends and data points identified
3. **Diversified**: Cover different aspects of the AI value chain
4. **Timely**: Relevant for the 1-2 year time horizon

Provide your analysis in the following JSON format:
{{
  "investment_themes": [
    {{
      "theme_name": "concise theme name",
      "description": "detailed description of the theme",
      "rationale": "why this theme is compelling based on the trends",
      "key_drivers": ["list of key drivers from the analysis"],
      "risk_factors": ["potential risks to consider"],
      "value_chain_position": "upstream|midstream|downstream",
      "time_horizon": "short-term|medium-term",
      "confidence_level": "high|medium|low",
      "supporting_data": ["specific data points supporting this theme"]
    }}
  ],
  "sector_breakdown": {{
    "semiconductors": "analysis of semiconductor opportunities",
    "hardware": "analysis of hardware/infrastructure opportunities",
    "cloud_compute": "analysis of cloud and compute opportunities",
    "software": "analysis of AI software opportunities",
    "data_infrastructure": "analysis of data infrastructure opportunities",
    "energy": "analysis of energy/power opportunities"
  }},
  "allocation_guidance": {{
    "high_conviction": ["theme names for higher allocation"],
    "medium_conviction": ["theme names for medium allocation"],
    "exploratory": ["theme names for smaller allocation"]
  }}
}}

Focus on themes that can be implemented through publicly traded stocks. Consider the entire AI value chain from chips to power to software."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                temperature=0.4,
                messages=[
                    {"role": "user", "content": themes_prompt}
                ]
            )

            response_text = response.content[0].text
            themes_result = self._extract_json_from_response(response_text)

            return themes_result

        except Exception as e:
            print(f"Error generating themes: {e}")
            return self._get_empty_themes()

    def _prepare_analysis_summary(self, trend_analysis: Dict) -> str:
        """Format trend analysis for theme generation."""
        summary_parts = []

        # Key trends
        summary_parts.append("KEY TRENDS:")
        for trend in trend_analysis.get('key_trends', []):
            summary_parts.append(f"\n- {trend.get('trend', 'N/A')}")
            summary_parts.append(f"  Evidence: {trend.get('evidence', 'N/A')}")
            summary_parts.append(f"  Importance: {trend.get('importance', 'N/A')}")

        # Data points
        summary_parts.append("\n\nDATA POINTS:")
        for dp in trend_analysis.get('data_points', []):
            summary_parts.append(f"\n- {dp.get('metric', 'N/A')}: {dp.get('value', 'N/A')}")
            summary_parts.append(f"  Context: {dp.get('context', 'N/A')}")

        # Supply chain insights
        summary_parts.append("\n\nSUPPLY CHAIN INSIGHTS:")
        for insight in trend_analysis.get('supply_chain_insights', []):
            summary_parts.append(f"\n- {insight.get('area', 'N/A')}")
            summary_parts.append(f"  Insight: {insight.get('insight', 'N/A')}")
            summary_parts.append(f"  Opportunity: {insight.get('opportunity', 'N/A')}")

        # Technology trends
        summary_parts.append("\n\nTECHNOLOGY TRENDS:")
        for tech in trend_analysis.get('technology_trends', []):
            summary_parts.append(f"\n- {tech.get('technology', 'N/A')} ({tech.get('adoption_stage', 'N/A')})")
            summary_parts.append(f"  Key Players: {', '.join(tech.get('key_players', []))}")
            summary_parts.append(f"  Investment Angle: {tech.get('investment_angle', 'N/A')}")

        return '\n'.join(summary_parts)

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from Claude's response."""
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            json_str = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            json_str = response_text[start:end].strip()
        else:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            return self._get_empty_themes()

    def _get_empty_themes(self) -> Dict:
        """Return empty themes structure."""
        return {
            "investment_themes": [],
            "sector_breakdown": {},
            "allocation_guidance": {
                "high_conviction": [],
                "medium_conviction": [],
                "exploratory": []
            }
        }

    def save_themes(self, themes: Dict, filename: str = 'data/investment_themes.json'):
        """Save themes to file."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(themes, f, indent=2, ensure_ascii=False)

        print(f"Investment themes saved to {filename}")

    def print_summary(self, themes: Dict):
        """Print a human-readable summary of themes."""
        print("\n" + "="*80)
        print("INVESTMENT THEMES SUMMARY")
        print("="*80)

        print(f"\n💼 Investment Themes ({len(themes.get('investment_themes', []))} identified):\n")

        for i, theme in enumerate(themes.get('investment_themes', []), 1):
            print(f"{i}. {theme.get('theme_name', 'N/A')}")
            print(f"   {theme.get('description', 'N/A')}")
            print(f"   Confidence: {theme.get('confidence_level', 'N/A')} | "
                  f"Position: {theme.get('value_chain_position', 'N/A')}")
            print(f"   Rationale: {theme.get('rationale', 'N/A')[:150]}...")
            print()

        allocation = themes.get('allocation_guidance', {})
        print("\n📊 Allocation Guidance:")
        print(f"   High Conviction: {', '.join(allocation.get('high_conviction', []))}")
        print(f"   Medium Conviction: {', '.join(allocation.get('medium_conviction', []))}")
        print(f"   Exploratory: {', '.join(allocation.get('exploratory', []))}")


if __name__ == "__main__":
    import sys

    # Load trend analysis
    try:
        with open('data/trend_analysis.json', 'r', encoding='utf-8') as f:
            trend_analysis = json.load(f)
    except FileNotFoundError:
        print("Error: data/trend_analysis.json not found. Run analyzer.py first.")
        sys.exit(1)

    # Generate themes
    generator = InvestmentThemeGenerator()
    themes = generator.generate_themes(trend_analysis)

    # Save and print
    generator.save_themes(themes)
    generator.print_summary(themes)
