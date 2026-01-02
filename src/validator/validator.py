"""
Ticker Validator Module
Validates tickers against recent news, market sentiment, and fundamentals.
"""

import json
import os
from typing import Dict, List, Optional
from anthropic import Anthropic
import yfinance as yf
from datetime import datetime, timedelta


class TickerValidator:
    """Validates ticker recommendations against multiple criteria."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the validator.

        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = Anthropic(api_key=self.api_key)

    def validate_tickers(self, ticker_recommendations: Dict, themes: Dict) -> Dict[str, any]:
        """
        Validate ticker recommendations.

        Args:
            ticker_recommendations: Output from TickerFinder
            themes: Original investment themes for context

        Returns:
            Validated ticker data with scores and recommendations
        """
        print("\nStarting ticker validation...")

        validated_tickers = []

        # Collect all unique tickers
        all_tickers = set()
        for theme_rec in ticker_recommendations.get('ticker_recommendations', []):
            for ticker_info in theme_rec.get('tickers', []):
                if ticker_info.get('validation_status') == 'valid':
                    all_tickers.add(ticker_info.get('symbol'))

        # Add portfolio candidates
        candidates = ticker_recommendations.get('portfolio_candidates', {})
        for category in ['core_holdings', 'satellite_holdings', 'exploratory_holdings']:
            all_tickers.update(candidates.get(category, []))

        print(f"Validating {len(all_tickers)} unique tickers...")

        # Validate each ticker
        for symbol in sorted(all_tickers):
            validation_result = self._validate_single_ticker(symbol, themes)
            if validation_result:
                validated_tickers.append(validation_result)

        # Analyze and score
        final_validation = self._analyze_portfolio_fit(
            validated_tickers,
            themes,
            ticker_recommendations
        )

        return final_validation

    def _validate_single_ticker(self, symbol: str, themes: Dict) -> Optional[Dict]:
        """
        Validate a single ticker.

        Args:
            symbol: Stock ticker symbol
            themes: Investment themes for context

        Returns:
            Validation results or None if failed
        """
        print(f"\n  Validating {symbol}...")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get recent price history
            hist = ticker.history(period="3mo")

            if hist.empty or not info:
                print(f"    ✗ No data available")
                return None

            # Calculate basic metrics
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if not current_price:
                print(f"    ✗ No price data")
                return None

            # Get news
            try:
                news = ticker.news[:5] if hasattr(ticker, 'news') else []
            except:
                news = []

            validation_data = {
                'symbol': symbol,
                'company_name': info.get('longName', info.get('shortName', symbol)),
                'current_price': current_price,
                'market_cap': info.get('marketCap'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'profit_margins': info.get('profitMargins'),
                'debt_to_equity': info.get('debtToEquity'),
                'beta': info.get('beta'),
                'analyst_recommendations': info.get('recommendationKey'),
                'target_mean_price': info.get('targetMeanPrice'),
                '52week_high': info.get('fiftyTwoWeekHigh'),
                '52week_low': info.get('fiftyTwoWeekLow'),
                'avg_volume': info.get('averageVolume'),
                'recent_news_count': len(news),
                'news_headlines': [n.get('title', '') for n in news[:3]],
                'validation_timestamp': datetime.now().isoformat()
            }

            # Calculate price momentum
            if len(hist) >= 20:
                validation_data['price_change_3mo'] = (
                    (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                )
                validation_data['price_change_1mo'] = (
                    (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100
                )

            print(f"    ✓ Data collected successfully")
            return validation_data

        except Exception as e:
            print(f"    ✗ Error: {e}")
            return None

    def _analyze_portfolio_fit(
        self,
        validated_tickers: List[Dict],
        themes: Dict,
        ticker_recommendations: Dict
    ) -> Dict:
        """
        Analyze how well tickers fit the portfolio using Claude.

        Args:
            validated_tickers: List of validated ticker data
            themes: Investment themes
            ticker_recommendations: Original ticker recommendations

        Returns:
            Final validation with scores and recommendations
        """
        print("\nAnalyzing portfolio fit with Claude...")

        # Prepare data for analysis
        tickers_summary = self._prepare_tickers_for_analysis(validated_tickers)
        themes_summary = self._prepare_themes_for_analysis(themes)

        analysis_prompt = f"""You are an expert portfolio analyst. Analyze the following validated stock tickers against the investment themes and provide a comprehensive validation.

INVESTMENT THEMES:
{themes_summary}

VALIDATED TICKERS:
{tickers_summary}

For each ticker, evaluate:
1. **Theme Alignment**: How well it matches the investment themes (score 1-10)
2. **Fundamental Quality**: Financial health and growth metrics (score 1-10)
3. **Market Sentiment**: Based on recent performance and analyst views (score 1-10)
4. **Risk Assessment**: Key risks and concerns
5. **Overall Recommendation**: Buy/Hold/Pass with rationale

Provide analysis in the following JSON format:
{{
  "ticker_analysis": [
    {{
      "symbol": "TICKER",
      "theme_alignment_score": 8,
      "theme_alignment_notes": "explanation",
      "fundamental_quality_score": 7,
      "fundamental_notes": "explanation",
      "market_sentiment_score": 6,
      "sentiment_notes": "explanation",
      "overall_score": 7.0,
      "recommendation": "Buy|Hold|Pass",
      "rationale": "detailed rationale",
      "key_risks": ["risk 1", "risk 2"],
      "key_strengths": ["strength 1", "strength 2"],
      "suggested_allocation": "high|medium|low|none"
    }}
  ],
  "portfolio_summary": {{
    "recommended_tickers": ["TICKER1", "TICKER2", ...],
    "conditional_tickers": ["TICKER3", ...],
    "excluded_tickers": ["TICKER4", ...],
    "diversification_notes": "assessment of portfolio diversification",
    "risk_assessment": "overall portfolio risk assessment",
    "expected_characteristics": "expected portfolio characteristics"
  }}
}}

Be critical and objective. Only recommend stocks that truly fit the themes and have solid fundamentals."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            response_text = response.content[0].text
            analysis_result = self._extract_json_from_response(response_text)

            # Combine original data with analysis
            final_result = {
                'validated_tickers': validated_tickers,
                'analysis': analysis_result,
                'validation_timestamp': datetime.now().isoformat()
            }

            return final_result

        except Exception as e:
            print(f"Error in analysis: {e}")
            return {
                'validated_tickers': validated_tickers,
                'analysis': {'ticker_analysis': [], 'portfolio_summary': {}},
                'validation_timestamp': datetime.now().isoformat()
            }

    def _prepare_tickers_for_analysis(self, validated_tickers: List[Dict]) -> str:
        """Format ticker data for analysis."""
        summary_parts = []

        for ticker in validated_tickers:
            summary_parts.append(f"\n{ticker['symbol']} - {ticker['company_name']}")
            summary_parts.append(f"  Sector: {ticker.get('sector', 'N/A')} | Industry: {ticker.get('industry', 'N/A')}")
            summary_parts.append(f"  Market Cap: ${ticker.get('market_cap', 0)/1e9:.1f}B")
            summary_parts.append(f"  Current Price: ${ticker.get('current_price', 'N/A')}")

            if ticker.get('pe_ratio'):
                summary_parts.append(f"  P/E: {ticker['pe_ratio']:.1f}")
            if ticker.get('revenue_growth'):
                summary_parts.append(f"  Revenue Growth: {ticker['revenue_growth']*100:.1f}%")
            if ticker.get('profit_margins'):
                summary_parts.append(f"  Profit Margin: {ticker['profit_margins']*100:.1f}%")
            if ticker.get('price_change_3mo'):
                summary_parts.append(f"  3M Price Change: {ticker['price_change_3mo']:.1f}%")

            if ticker.get('analyst_recommendations'):
                summary_parts.append(f"  Analyst Rec: {ticker['analyst_recommendations']}")

            if ticker.get('news_headlines'):
                summary_parts.append(f"  Recent News: {', '.join(ticker['news_headlines'][:2])}")

        return '\n'.join(summary_parts)

    def _prepare_themes_for_analysis(self, themes: Dict) -> str:
        """Format themes for analysis."""
        summary_parts = []

        for theme in themes.get('investment_themes', []):
            summary_parts.append(f"\n- {theme.get('theme_name', 'N/A')}")
            summary_parts.append(f"  {theme.get('description', 'N/A')}")
            summary_parts.append(f"  Confidence: {theme.get('confidence_level', 'N/A')}")

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
            return {'ticker_analysis': [], 'portfolio_summary': {}}

    def save_validation(self, validation: Dict, filename: str = 'data/ticker_validation.json'):
        """Save validation results to file."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(validation, f, indent=2, ensure_ascii=False)

        print(f"\nValidation results saved to {filename}")

    def print_summary(self, validation: Dict):
        """Print a human-readable summary of validation results."""
        print("\n" + "="*80)
        print("TICKER VALIDATION SUMMARY")
        print("="*80)

        analysis = validation.get('analysis', {})
        ticker_analysis = analysis.get('ticker_analysis', [])

        # Sort by overall score
        sorted_analysis = sorted(
            ticker_analysis,
            key=lambda x: x.get('overall_score', 0),
            reverse=True
        )

        print(f"\n📊 Analyzed {len(sorted_analysis)} tickers\n")

        for ta in sorted_analysis:
            symbol = ta.get('symbol', 'N/A')
            rec = ta.get('recommendation', 'N/A')
            score = ta.get('overall_score', 0)

            rec_emoji = "🟢" if rec == "Buy" else "🟡" if rec == "Hold" else "🔴"

            print(f"{rec_emoji} {symbol} - {rec} (Score: {score}/10)")
            print(f"   Theme Alignment: {ta.get('theme_alignment_score', 'N/A')}/10 | "
                  f"Fundamentals: {ta.get('fundamental_quality_score', 'N/A')}/10 | "
                  f"Sentiment: {ta.get('market_sentiment_score', 'N/A')}/10")
            print(f"   Rationale: {ta.get('rationale', 'N/A')[:120]}...")
            print()

        summary = analysis.get('portfolio_summary', {})
        print("\n💼 Portfolio Recommendations:")
        print(f"   Recommended: {', '.join(summary.get('recommended_tickers', []))}")
        print(f"   Conditional: {', '.join(summary.get('conditional_tickers', []))}")
        print(f"   Excluded: {', '.join(summary.get('excluded_tickers', []))}")

        if summary.get('risk_assessment'):
            print(f"\n⚠️  Risk Assessment:")
            print(f"   {summary['risk_assessment']}")


if __name__ == "__main__":
    import sys

    # Load ticker recommendations
    try:
        with open('data/ticker_recommendations.json', 'r', encoding='utf-8') as f:
            ticker_recommendations = json.load(f)
    except FileNotFoundError:
        print("Error: data/ticker_recommendations.json not found.")
        sys.exit(1)

    # Load investment themes
    try:
        with open('data/investment_themes.json', 'r', encoding='utf-8') as f:
            themes = json.load(f)
    except FileNotFoundError:
        print("Error: data/investment_themes.json not found.")
        sys.exit(1)

    # Validate
    validator = TickerValidator()
    validation = validator.validate_tickers(ticker_recommendations, themes)

    # Save and print
    validator.save_validation(validation)
    validator.print_summary(validation)
