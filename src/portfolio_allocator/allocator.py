"""
Portfolio Allocator Module
Calculates optimal portfolio weights based on validated tickers.
"""

import json
import os
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from anthropic import Anthropic


class PortfolioAllocator:
    """Calculates portfolio allocations based on validated ticker analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the portfolio allocator.

        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = Anthropic(api_key=self.api_key)

    def allocate_portfolio(
        self,
        validation_results: Dict,
        themes: Dict,
        total_capital: float = 100000.0,
        max_positions: int = 15
    ) -> Dict[str, any]:
        """
        Calculate portfolio allocations.

        Args:
            validation_results: Output from TickerValidator
            themes: Investment themes
            total_capital: Total capital to allocate
            max_positions: Maximum number of positions

        Returns:
            Portfolio allocation with weights and dollar amounts
        """
        print(f"\nCalculating portfolio allocation for ${total_capital:,.0f}...")

        # Extract recommended tickers from validation
        analysis = validation_results.get('analysis', {})
        ticker_analysis = analysis.get('ticker_analysis', [])

        # Filter for Buy recommendations with good scores
        buy_tickers = [
            ta for ta in ticker_analysis
            if ta.get('recommendation') == 'Buy' and ta.get('overall_score', 0) >= 6.0
        ]

        # Sort by overall score
        buy_tickers = sorted(
            buy_tickers,
            key=lambda x: x.get('overall_score', 0),
            reverse=True
        )[:max_positions]

        if not buy_tickers:
            print("No Buy recommendations found with sufficient scores.")
            return self._get_empty_allocation()

        # Use Claude to determine optimal allocation strategy
        allocation_strategy = self._get_allocation_strategy(
            buy_tickers,
            themes,
            validation_results
        )

        # Calculate specific allocations
        portfolio = self._calculate_allocations(
            buy_tickers,
            allocation_strategy,
            total_capital
        )

        return portfolio

    def _get_allocation_strategy(
        self,
        buy_tickers: List[Dict],
        themes: Dict,
        validation_results: Dict
    ) -> Dict:
        """
        Use Claude to determine allocation strategy.

        Args:
            buy_tickers: List of Buy-rated tickers
            themes: Investment themes
            validation_results: Full validation results

        Returns:
            Allocation strategy with weights
        """
        print("Determining allocation strategy with Claude...")

        # Prepare summary
        tickers_summary = self._prepare_tickers_summary(buy_tickers)
        themes_summary = self._prepare_themes_summary(themes)

        allocation_prompt = f"""You are an expert portfolio manager specializing in technology and AI investments. Based on the validated stock analysis, determine optimal portfolio allocation weights.

INVESTMENT THEMES:
{themes_summary}

BUY-RATED STOCKS:
{tickers_summary}

Determine portfolio weights considering:
1. **Risk/Reward Balance**: Balance high-conviction plays with diversification
2. **Theme Exposure**: Ensure coverage across key themes
3. **Position Sizing**: Larger positions for higher-conviction, lower-risk plays
4. **Diversification**: Avoid over-concentration in any single sector or theme
5. **Liquidity**: Consider market cap and trading volume

Provide allocation in the following JSON format:
{{
  "allocation_strategy": "description of overall strategy",
  "allocation_tiers": {{
    "core": {{
      "weight_range": "40-60%",
      "description": "Highest conviction, lowest risk",
      "tickers": ["TICKER1", "TICKER2"]
    }},
    "satellite": {{
      "weight_range": "30-40%",
      "description": "Strong conviction, moderate risk",
      "tickers": ["TICKER3", "TICKER4"]
    }},
    "tactical": {{
      "weight_range": "10-20%",
      "description": "Opportunistic, higher risk/reward",
      "tickers": ["TICKER5", "TICKER6"]
    }}
  }},
  "ticker_weights": [
    {{
      "symbol": "TICKER",
      "weight_percent": 15.0,
      "rationale": "why this weight",
      "tier": "core|satellite|tactical"
    }}
  ],
  "rebalancing_guidance": {{
    "frequency": "monthly|quarterly",
    "triggers": ["conditions that would trigger rebalancing"],
    "exit_criteria": ["conditions for exiting positions"]
  }},
  "risk_management": {{
    "max_single_position": 20.0,
    "max_sector_exposure": 40.0,
    "cash_buffer": 5.0,
    "notes": "risk management considerations"
  }}
}}

Total portfolio weights must sum to 100% (or slightly less to maintain cash buffer).
Provide specific weight for each ticker, ensuring proper diversification."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": allocation_prompt}
                ]
            )

            response_text = response.content[0].text
            strategy = self._extract_json_from_response(response_text)

            return strategy

        except Exception as e:
            print(f"Error getting allocation strategy: {e}")
            # Fallback to equal-weight
            return self._get_equal_weight_strategy(buy_tickers)

    def _calculate_allocations(
        self,
        buy_tickers: List[Dict],
        allocation_strategy: Dict,
        total_capital: float
    ) -> Dict:
        """
        Calculate specific dollar allocations.

        Args:
            buy_tickers: List of tickers to include
            allocation_strategy: Strategy from Claude
            total_capital: Total capital to allocate

        Returns:
            Portfolio with specific allocations
        """
        ticker_weights = allocation_strategy.get('ticker_weights', [])

        # Create allocation list
        allocations = []

        for tw in ticker_weights:
            symbol = tw.get('symbol')
            weight_pct = tw.get('weight_percent', 0)

            # Find ticker data
            ticker_data = next((t for t in buy_tickers if t.get('symbol') == symbol), None)

            if ticker_data:
                dollar_amount = total_capital * (weight_pct / 100.0)

                allocation = {
                    'symbol': symbol,
                    'weight_percent': weight_pct,
                    'dollar_allocation': dollar_amount,
                    'tier': tw.get('tier', 'unknown'),
                    'rationale': tw.get('rationale', ''),
                    'overall_score': ticker_data.get('overall_score', 0),
                    'theme_alignment': ticker_data.get('theme_alignment_score', 0),
                    'fundamental_score': ticker_data.get('fundamental_quality_score', 0)
                }

                allocations.append(allocation)

        # Calculate totals
        total_weight = sum(a['weight_percent'] for a in allocations)
        total_allocated = sum(a['dollar_allocation'] for a in allocations)
        cash_remaining = total_capital - total_allocated

        portfolio = {
            'allocations': allocations,
            'summary': {
                'total_capital': total_capital,
                'total_allocated': total_allocated,
                'cash_remaining': cash_remaining,
                'total_weight': total_weight,
                'number_of_positions': len(allocations)
            },
            'allocation_strategy': allocation_strategy.get('allocation_strategy', ''),
            'allocation_tiers': allocation_strategy.get('allocation_tiers', {}),
            'rebalancing_guidance': allocation_strategy.get('rebalancing_guidance', {}),
            'risk_management': allocation_strategy.get('risk_management', {}),
            'creation_date': pd.Timestamp.now().isoformat()
        }

        return portfolio

    def _prepare_tickers_summary(self, buy_tickers: List[Dict]) -> str:
        """Format tickers for allocation prompt."""
        summary_parts = []

        for ticker in buy_tickers:
            summary_parts.append(f"\n{ticker.get('symbol', 'N/A')}")
            summary_parts.append(f"  Overall Score: {ticker.get('overall_score', 0)}/10")
            summary_parts.append(f"  Theme Alignment: {ticker.get('theme_alignment_score', 0)}/10")
            summary_parts.append(f"  Fundamentals: {ticker.get('fundamental_quality_score', 0)}/10")
            summary_parts.append(f"  Sentiment: {ticker.get('market_sentiment_score', 0)}/10")
            summary_parts.append(f"  Suggested Allocation: {ticker.get('suggested_allocation', 'N/A')}")
            summary_parts.append(f"  Rationale: {ticker.get('rationale', 'N/A')[:100]}...")

        return '\n'.join(summary_parts)

    def _prepare_themes_summary(self, themes: Dict) -> str:
        """Format themes for allocation prompt."""
        summary_parts = []

        allocation_guidance = themes.get('allocation_guidance', {})
        summary_parts.append("Allocation Guidance:")
        summary_parts.append(f"  High Conviction: {', '.join(allocation_guidance.get('high_conviction', []))}")
        summary_parts.append(f"  Medium Conviction: {', '.join(allocation_guidance.get('medium_conviction', []))}")
        summary_parts.append(f"  Exploratory: {', '.join(allocation_guidance.get('exploratory', []))}")

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
            return {}

    def _get_equal_weight_strategy(self, buy_tickers: List[Dict]) -> Dict:
        """Fallback equal-weight strategy."""
        n_tickers = len(buy_tickers)
        weight_each = 95.0 / n_tickers  # 95% invested, 5% cash

        ticker_weights = [
            {
                'symbol': t.get('symbol'),
                'weight_percent': weight_each,
                'rationale': 'Equal weight allocation',
                'tier': 'core'
            }
            for t in buy_tickers
        ]

        return {
            'allocation_strategy': 'Equal weight allocation across all Buy recommendations',
            'ticker_weights': ticker_weights,
            'risk_management': {
                'max_single_position': weight_each,
                'cash_buffer': 5.0
            }
        }

    def _get_empty_allocation(self) -> Dict:
        """Return empty allocation structure."""
        return {
            'allocations': [],
            'summary': {
                'total_capital': 0,
                'total_allocated': 0,
                'cash_remaining': 0,
                'total_weight': 0,
                'number_of_positions': 0
            }
        }

    def save_portfolio(self, portfolio: Dict, filename: str = 'data/portfolio_allocation.json'):
        """Save portfolio allocation to file."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(portfolio, f, indent=2, ensure_ascii=False)

        print(f"\nPortfolio allocation saved to {filename}")

    def export_to_csv(self, portfolio: Dict, filename: str = 'data/portfolio_allocation.csv'):
        """Export portfolio to CSV for easy viewing."""
        allocations = portfolio.get('allocations', [])

        if not allocations:
            print("No allocations to export.")
            return

        df = pd.DataFrame(allocations)
        df = df.sort_values('weight_percent', ascending=False)

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False)

        print(f"Portfolio exported to CSV: {filename}")

    def print_summary(self, portfolio: Dict):
        """Print a human-readable portfolio summary."""
        print("\n" + "="*80)
        print("PORTFOLIO ALLOCATION")
        print("="*80)

        summary = portfolio.get('summary', {})
        print(f"\n💰 Total Capital: ${summary.get('total_capital', 0):,.2f}")
        print(f"📊 Total Allocated: ${summary.get('total_allocated', 0):,.2f}")
        print(f"💵 Cash Remaining: ${summary.get('cash_remaining', 0):,.2f}")
        print(f"🎯 Number of Positions: {summary.get('number_of_positions', 0)}")

        allocations = portfolio.get('allocations', [])
        if allocations:
            print("\n" + "-"*80)
            print("POSITION DETAILS")
            print("-"*80)

            # Group by tier
            tiers = {}
            for alloc in allocations:
                tier = alloc.get('tier', 'unknown')
                if tier not in tiers:
                    tiers[tier] = []
                tiers[tier].append(alloc)

            for tier_name in ['core', 'satellite', 'tactical', 'unknown']:
                if tier_name in tiers:
                    tier_allocations = tiers[tier_name]
                    tier_weight = sum(a['weight_percent'] for a in tier_allocations)

                    print(f"\n{tier_name.upper()} ({tier_weight:.1f}%):")

                    for alloc in sorted(tier_allocations, key=lambda x: x['weight_percent'], reverse=True):
                        print(f"\n  {alloc['symbol']}")
                        print(f"    Weight: {alloc['weight_percent']:.1f}% | "
                              f"Amount: ${alloc['dollar_allocation']:,.2f}")
                        print(f"    Score: {alloc['overall_score']:.1f}/10 "
                              f"(Theme: {alloc['theme_alignment']}/10, "
                              f"Fundamentals: {alloc['fundamental_score']}/10)")
                        print(f"    Rationale: {alloc['rationale'][:100]}...")

        strategy = portfolio.get('allocation_strategy', '')
        if strategy:
            print(f"\n📋 Strategy: {strategy}")

        rebalancing = portfolio.get('rebalancing_guidance', {})
        if rebalancing:
            print(f"\n🔄 Rebalancing: {rebalancing.get('frequency', 'N/A')}")

        risk_mgmt = portfolio.get('risk_management', {})
        if risk_mgmt:
            print(f"\n⚠️  Risk Management:")
            print(f"    Max Single Position: {risk_mgmt.get('max_single_position', 'N/A')}%")
            print(f"    Max Sector Exposure: {risk_mgmt.get('max_sector_exposure', 'N/A')}%")
            print(f"    Cash Buffer: {risk_mgmt.get('cash_buffer', 'N/A')}%")


if __name__ == "__main__":
    import sys

    # Load validation results
    try:
        with open('data/ticker_validation.json', 'r', encoding='utf-8') as f:
            validation_results = json.load(f)
    except FileNotFoundError:
        print("Error: data/ticker_validation.json not found.")
        sys.exit(1)

    # Load themes
    try:
        with open('data/investment_themes.json', 'r', encoding='utf-8') as f:
            themes = json.load(f)
    except FileNotFoundError:
        print("Error: data/investment_themes.json not found.")
        sys.exit(1)

    # Allocate portfolio
    allocator = PortfolioAllocator()
    portfolio = allocator.allocate_portfolio(validation_results, themes)

    # Save and print
    allocator.save_portfolio(portfolio)
    allocator.export_to_csv(portfolio)
    allocator.print_summary(portfolio)
