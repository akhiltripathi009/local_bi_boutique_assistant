"""
competitor_analysis.py
Comprehensive competitive intelligence and dynamic pricing elasticity engine.
Analyzes internal pricing strategies against external luxury and contemporary benchmarks,
projects demand elasticity, and models margin expansion opportunities.
"""
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
try:
    from src.core.logger import setup_logging
    from src.core.catalog import CATALOG
    from src.data.db_manager import DatabaseManager
except ImportError:
    from logger_config import setup_logging
    # CATALOG imported at top-level
    # DatabaseManager imported at top-level


logger = setup_logging("competitor_analysis")


class CompetitorAnalyzer:
    """
    Advanced retail pricing intelligence and price elasticity simulation engine.
    
    Working:
    - Calculates category-weighted price elasticity of demand:
        % Volume Change = Elasticity * % Price Change
        Projected Units = Base Volume * (1 + % Volume Change)
    - Models the Competitor Price Index (CPI):
        CPI = (Your Price / Market Reference Price) * 100
    - Identifies underpriced margin expansion opportunities where current prices sit below
      contemporary and luxury benchmarks without consumer pushback.
      
    Why Required:
    - Boutique retailers often underprice core high-demand apparel (e.g. Italian linen, cashmere),
      leaving substantial gross margin on the table, or overprice seasonal basics, dampening sell-through.
      This engine prescribes safe repricing points that maximize gross profit dollars.
    """

    # Category-specific price elasticity of demand (retail fashion benchmarks)
    # Luxury outerwear is least price elastic (-1.10), casual tops are most price elastic (-1.55)
    CATEGORY_ELASTICITIES = {
        "Outerwear": -1.10,
        "Knitwear": -1.25,
        "Dresses": -1.35,
        "Bottoms": -1.40,
        "Tops": -1.55,
        "Apparel": -1.30
    }

    def __init__(self, competitor_df: Optional[pd.DataFrame] = None):
        """
        Initializes the analyzer with competitor benchmark data.
        
        Args:
            competitor_df: Dataframe with product_id, product_name, your_price,
                           competitor prices, pricing_index, and position.
        """
        self.df = competitor_df if competitor_df is not None else pd.DataFrame()

    @classmethod
    def get_store_cpi_metrics(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates store-wide Competitor Price Index (CPI) metrics and financial opportunities.
        
        Args:
            df: Dataframe from database_manager.fetch_dynamic_competitor_pricing()
            
        Returns:
            Dict containing store CPI, hazard counts, and margin opportunities.
        """
        try:
            if df.empty or "pricing_index" not in df.columns:
                return {
                    "store_cpi": 100.0,
                    "store_position": "Market Aligned",
                    "underpriced_count": 0,
                    "premium_count": 0,
                    "market_aligned_count": 0,
                    "total_margin_opportunity": 0.0,
                    "top_underpriced": [],
                    "top_premium": []
                }

            store_cpi = round(float(df["pricing_index"].mean()), 1)
            underpriced = df[df["pricing_index"] < 92.0]
            premium = df[df["pricing_index"] > 112.0]
            aligned = df[(df["pricing_index"] >= 92.0) & (df["pricing_index"] <= 112.0)]

            # Estimate total unearned margin across underpriced items assuming a baseline of 40 units/month each
            est_units_per_month = 40
            total_margin_opp = 0.0
            if "margin_gap" in df.columns:
                total_margin_opp = float((underpriced["margin_gap"] * est_units_per_month).sum())

            store_pos = "Market Aligned"
            if store_cpi < 95.0:
                store_pos = "Aggressively Value Positioned (Underpriced Gap)"
            elif store_cpi > 105.0:
                store_pos = "Premium Positioned (Luxury Tier)"

            top_underpriced_records = underpriced.head(4).to_dict(orient="records") if not underpriced.empty else []
            top_premium_records = premium.head(4).to_dict(orient="records") if not premium.empty else []

            return {
                "store_cpi": store_cpi,
                "store_position": store_pos,
                "underpriced_count": len(underpriced),
                "premium_count": len(premium),
                "market_aligned_count": len(aligned),
                "total_margin_opportunity": round(total_margin_opp, 2),
                "top_underpriced": top_underpriced_records,
                "top_premium": top_premium_records
            }
        except Exception as e:
            logger.error(f"Error calculating store CPI metrics: {e}")
            return {
                "store_cpi": 100.0,
                "store_position": "Market Aligned",
                "underpriced_count": 0,
                "premium_count": 0,
                "market_aligned_count": 0,
                "total_margin_opportunity": 0.0,
                "top_underpriced": [],
                "top_premium": []
            }

    @classmethod
    def simulate_price_elasticity(
        cls,
        product_id: str,
        old_price: float,
        new_price: float,
        cost: float,
        base_volume: int = 40,
        category: str = "Apparel",
        avg_market_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Simulates the financial and demand impact of a proposed price adjustment using
        fashion category price elasticity of demand coefficients.
        
        Args:
            product_id: Product SKU identifier
            old_price: Current retail price
            new_price: Proposed adjusted retail price
            cost: Unit cost basis
            base_volume: Estimated monthly sales volume in units
            category: Product category for elasticity lookups
            avg_market_price: Current competitor market average price
            
        Returns:
            Dict containing projected units, revenue, gross margin, profit delta, and new CPI.
        """
        try:
            old_price = float(old_price)
            new_price = float(new_price)
            cost = float(cost)
            base_volume = int(base_volume)
            elasticity = cls.CATEGORY_ELASTICITIES.get(category, -1.30)

            pct_price_change = (new_price - old_price) / old_price if old_price > 0 else 0.0
            pct_volume_change = elasticity * pct_price_change
            projected_units = max(1, int(round(base_volume * (1.0 + pct_volume_change))))

            # Baseline monthly financials
            old_revenue = round(old_price * base_volume, 2)
            old_cost = round(cost * base_volume, 2)
            old_gross_profit = round(old_revenue - old_cost, 2)
            old_margin_pct = round((old_gross_profit / old_revenue) * 100, 1) if old_revenue > 0 else 0.0

            # Projected monthly financials
            new_revenue = round(new_price * projected_units, 2)
            new_cost = round(cost * projected_units, 2)
            new_gross_profit = round(new_revenue - new_cost, 2)
            new_margin_pct = round((new_gross_profit / new_revenue) * 100, 1) if new_revenue > 0 else 0.0

            profit_delta = round(new_gross_profit - old_gross_profit, 2)
            revenue_delta = round(new_revenue - old_revenue, 2)
            volume_delta = projected_units - base_volume

            # Price index calculation
            market_ref = avg_market_price if avg_market_price and avg_market_price > 0 else old_price
            new_cpi = round((new_price / market_ref) * 100, 1)
            if new_cpi < 92.0:
                new_pos = "Underpriced Hazard"
            elif new_cpi > 112.0:
                new_pos = "Premium Positioned"
            else:
                new_pos = "Market Aligned"

            return {
                "product_id": product_id,
                "old_price": old_price,
                "new_price": new_price,
                "pct_price_change": round(pct_price_change * 100, 1),
                "elasticity": elasticity,
                "base_volume": base_volume,
                "projected_units": projected_units,
                "volume_delta": volume_delta,
                "pct_volume_change": round(pct_volume_change * 100, 1),
                "old_revenue": old_revenue,
                "new_revenue": new_revenue,
                "revenue_delta": revenue_delta,
                "old_gross_profit": old_gross_profit,
                "new_gross_profit": new_gross_profit,
                "profit_delta": profit_delta,
                "old_margin_pct": old_margin_pct,
                "new_margin_pct": new_margin_pct,
                "new_cpi": new_cpi,
                "new_position": new_pos,
                "is_profitable": profit_delta > 0
            }
        except Exception as e:
            logger.error(f"Error in simulate_price_elasticity: {e}")
            return {
                "product_id": product_id,
                "old_price": old_price,
                "new_price": new_price,
                "profit_delta": 0.0,
                "is_profitable": True
            }

    @classmethod
    def get_top_repricing_recommendations(cls, df: pd.DataFrame, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Generates actionable repricing recommendations with projected profit upside.
        
        Args:
            df: Dataframe from database_manager.fetch_dynamic_competitor_pricing()
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommendation dicts.
        """
        try:
            if df.empty:
                return []

            recs = []
            underpriced = df[df["pricing_index"] < 92.0]
            for _, row in underpriced.head(limit).iterrows():
                pid = str(row.get("product_id", ""))
                pname = str(row.get("product_name", ""))
                curr_p = float(row.get("your_price", 0.0))
                rec_p = float(row.get("recommended_price", curr_p))
                m_gap = float(row.get("margin_gap", 0.0))
                cat = str(row.get("category", "Apparel"))
                cost = float(row.get("cost", curr_p * 0.45))
                v_vine = float(row.get("velvet_vine_price", curr_p * 1.25))
                ave_app = float(row.get("avenue_price", curr_p * 1.05))

                sim = cls.simulate_price_elasticity(
                    product_id=pid,
                    old_price=curr_p,
                    new_price=rec_p,
                    cost=cost,
                    base_volume=40,
                    category=cat,
                    avg_market_price=float(row.get("avg_market_price", curr_p))
                )

                recs.append({
                    "product_id": pid,
                    "product_name": pname,
                    "current_price": curr_p,
                    "recommended_price": rec_p,
                    "price_increase": round(rec_p - curr_p, 2),
                    "pct_increase": round(((rec_p - curr_p) / curr_p) * 100, 1) if curr_p > 0 else 0.0,
                    "velvet_vine_price": v_vine,
                    "avenue_price": ave_app,
                    "projected_monthly_profit_gain": sim.get("profit_delta", round(m_gap * 40, 2)),
                    "rationale": (
                        f"Currently at ${curr_p:.2f} (CPI {row.get('pricing_index')}%), well below Velvet & Vine (${v_vine:.2f}) "
                        f"and Avenue Apparel (${ave_app:.2f}). Elevating to ${rec_p:.2f} preserves competitive appeal while unlocking "
                        f"estimated +${sim.get('profit_delta', round(m_gap * 40, 2)):,.2f} in net monthly profit."
                    )
                })

            return recs
        except Exception as e:
            logger.error(f"Error generating repricing recommendations: {e}")
            return []
