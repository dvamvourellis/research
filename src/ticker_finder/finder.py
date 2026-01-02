"""
Ticker Finder Module
Identifies stock tickers matching investment themes.
"""

import json
import os
from typing import Dict, List, Optional
from anthropic import Anthropic
import yfinance as yf


class TickerFinder:
    """Finds stock tickers matching investment themes."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ticker finder.

        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = Anthropic(api_key=self.api_key)

    def find_tickers(self, themes: Dict) -> Dict[str, any]:
        """
        Find stock tickers matching investment themes.

        Args:
            themes: Output from InvestmentThemeGenerator

        Returns:
            Dictionary containing ticker recommendations
        """
        themes_summary = self._prepare_themes_summary(themes)

        ticker_prompt = f"""You are an expert equity analyst with deep knowledge of publicly traded companies in AI, semiconductors, hardware, and technology sectors.

Based on the following investment themes, identify specific publicly traded stocks (US exchanges preferred, but include key international stocks if highly relevant).

Investment Themes:
{themes_summary}

For each theme, identify 3-8 specific stocks that best match the theme. Consider:
1. **Direct Exposure**: Companies with clear, direct exposure to the theme
2. **Market Position**: Leading companies with competitive advantages
3. **Financial Health**: Companies with solid fundamentals
4. **Liquidity**: Stocks with reasonable trading volume
5. **Diversification**: Mix of large-cap, mid-cap for diversification

Provide recommendations in the following JSON format:
{{
  "ticker_recommendations": [
    {{
      "theme_name": "matching theme name",
      "tickers": [
        {{
          "symbol": "TICKER",
          "company_name": "Company Name",
          "rationale": "why this stock fits the theme",
          "market_cap_category": "large-cap|mid-cap|small-cap",
          "exposure_type": "pure-play|diversified|indirect",
          "key_products": ["relevant products/services"],
          "competitive_advantages": ["list of advantages"]
        }}
      ]
    }}
  ],
  "portfolio_candidates": {{
    "core_holdings": ["TICKER1", "TICKER2", ...],
    "satellite_holdings": ["TICKER3", "TICKER4", ...],
    "exploratory_holdings": ["TICKER5", "TICKER6", ...]
  }}
}}

Focus on well-known, liquid stocks. Include ticker symbols that are valid for US markets (NYSE, NASDAQ) or major international exchanges."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": ticker_prompt}
                ]
            )

            response_text = response.content[0].text
            ticker_result = self._extract_json_from_response(response_text)

            # Validate tickers
            validated_result = self._validate_tickers(ticker_result)

            return validated_result

        except Exception as e:
            print(f"Error finding tickers: {e}")
            return self._get_empty_tickers()

    def _prepare_themes_summary(self, themes: Dict) -> str:
        """Format themes for ticker identification."""
        summary_parts = []

        for theme in themes.get('investment_themes', []):
            summary_parts.append(f"\nTHEME: {theme.get('theme_name', 'N/A')}")
            summary_parts.append(f"Description: {theme.get('description', 'N/A')}")
            summary_parts.append(f"Rationale: {theme.get('rationale', 'N/A')}")
            summary_parts.append(f"Key Drivers: {', '.join(theme.get('key_drivers', []))}")
            summary_parts.append(f"Value Chain: {theme.get('value_chain_position', 'N/A')}")
            summary_parts.append(f"Confidence: {theme.get('confidence_level', 'N/A')}")

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
            return self._get_empty_tickers()

    def _validate_tickers(self, ticker_result: Dict) -> Dict:
        """
        Validate that tickers exist and are tradeable.

        Args:
            ticker_result: Raw ticker recommendations

        Returns:
            Validated ticker recommendations with additional info
        """
        print("\nValidating tickers...")

        validated_recommendations = []

        for theme_rec in ticker_result.get('ticker_recommendations', []):
            validated_tickers = []

            for ticker_info in theme_rec.get('tickers', []):
                symbol = ticker_info.get('symbol', '')

                try:
                    # Fetch ticker info from yfinance
                    ticker = yf.Ticker(symbol)
                    info = ticker.info

                    # Check if ticker is valid (has basic info)
                    if info and 'regularMarketPrice' in info or 'currentPrice' in info:
                        # Add validation status and market data
                        ticker_info['validation_status'] = 'valid'
                        ticker_info['current_price'] = info.get('currentPrice') or info.get('regularMarketPrice')
                        ticker_info['market_cap'] = info.get('marketCap')
                        ticker_info['sector'] = info.get('sector', 'N/A')
                        ticker_info['industry'] = info.get('industry', 'N/A')

                        validated_tickers.append(ticker_info)
                        print(f"  ✓ {symbol}: Valid")
                    else:
                        print(f"  ✗ {symbol}: Invalid or insufficient data")
                        ticker_info['validation_status'] = 'invalid'

                except Exception as e:
                    print(f"  ✗ {symbol}: Error - {e}")
                    ticker_info['validation_status'] = 'error'
                    ticker_info['error_message'] = str(e)

            if validated_tickers:
                theme_rec['tickers'] = validated_tickers
                validated_recommendations.append(theme_rec)

        ticker_result['ticker_recommendations'] = validated_recommendations

        # Validate portfolio candidates
        portfolio_candidates = ticker_result.get('portfolio_candidates', {})
        for category in ['core_holdings', 'satellite_holdings', 'exploratory_holdings']:
            if category in portfolio_candidates:
                validated = []
                for symbol in portfolio_candidates[category]:
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        if info and ('regularMarketPrice' in info or 'currentPrice' in info):
                            validated.append(symbol)
                            print(f"  ✓ {symbol} ({category}): Valid")
                    except:
                        print(f"  ✗ {symbol} ({category}): Invalid")

                portfolio_candidates[category] = validated

        return ticker_result

    def _get_empty_tickers(self) -> Dict:
        """Return empty tickers structure."""
        return {
            "ticker_recommendations": [],
            "portfolio_candidates": {
                "core_holdings": [],
                "satellite_holdings": [],
                "exploratory_holdings": []
            }
        }

    def save_tickers(self, tickers: Dict, filename: str = 'data/ticker_recommendations.json'):
        """Save ticker recommendations to file."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(tickers, f, indent=2, ensure_ascii=False)

        print(f"\nTicker recommendations saved to {filename}")

    def print_summary(self, tickers: Dict):
        """Print a human-readable summary of ticker recommendations."""
        print("\n" + "="*80)
        print("TICKER RECOMMENDATIONS SUMMARY")
        print("="*80)

        for theme_rec in tickers.get('ticker_recommendations', []):
            print(f"\n📈 Theme: {theme_rec.get('theme_name', 'N/A')}")
            print(f"   Tickers: {len(theme_rec.get('tickers', []))} identified\n")

            for ticker_info in theme_rec.get('tickers', []):
                symbol = ticker_info.get('symbol', 'N/A')
                name = ticker_info.get('company_name', 'N/A')
                status = ticker_info.get('validation_status', 'unknown')

                if status == 'valid':
                    price = ticker_info.get('current_price', 'N/A')
                    market_cap = ticker_info.get('market_cap', 0)
                    market_cap_str = f"${market_cap/1e9:.1f}B" if market_cap else "N/A"

                    print(f"   ✓ {symbol} - {name}")
                    print(f"      Price: ${price} | Market Cap: {market_cap_str}")
                    print(f"      Rationale: {ticker_info.get('rationale', 'N/A')[:100]}...")
                    print()

        candidates = tickers.get('portfolio_candidates', {})
        print("\n💼 Portfolio Structure:")
        print(f"   Core Holdings: {', '.join(candidates.get('core_holdings', []))}")
        print(f"   Satellite Holdings: {', '.join(candidates.get('satellite_holdings', []))}")
        print(f"   Exploratory: {', '.join(candidates.get('exploratory_holdings', []))}")


if __name__ == "__main__":
    import sys

    # Load investment themes
    try:
        with open('data/investment_themes.json', 'r', encoding='utf-8') as f:
            themes = json.load(f)
    except FileNotFoundError:
        print("Error: data/investment_themes.json not found. Run theme_generator.py first.")
        sys.exit(1)

    # Find tickers
    finder = TickerFinder()
    tickers = finder.find_tickers(themes)

    # Save and print
    finder.save_tickers(tickers)
    finder.print_summary(tickers)
