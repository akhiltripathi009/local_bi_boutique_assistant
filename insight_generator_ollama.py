import json
import ollama
import logging
from typing import Dict, Any
from logger_config import setup_logging

logger = setup_logging("insight_generator")

class LocalOllamaBoutiqueAnalyst:
    """
    AI-driven business analyst leveraging local Ollama models.
    Generates strategic insights from inventory, sales, and sentiment data.
    """
    def __init__(self, model_name: str = "llama3.2:3b"):
        """
        Initializes the analyst with a specific local model.
        
        Args:
            model_name (str): The name of the Ollama model to use. Defaults to "llama3.2:3b".
        """
        self.model_name = model_name

    def generate_boutique_strategy(self, consolidated_payload: Dict[str, Any]) -> str:
        """
        Analyzes business metrics and generates a health report.
        
        Args:
            consolidated_payload (Dict): The data to be analyzed (sales, inventory, sentiment).
            
        Returns:
            str: A markdown-formatted strategy report.
        """
        prompt = f"""
        You are an elite Retail Merchandise Manager specializing in luxury independent apparel boutiques.
        Analyze the verified processing metrics below and generate a business health report.

        DATA LIFECYCLE PAYLOAD:
        {json.dumps(consolidated_payload, indent=2)}

        REQUIRED MARKDOWN FORMAT FOR THE OWNER:
        Use clear headers and short, scannable summaries. Include these sections:
        
        ###  Kleid 1. Merchandise Performance & Sell-Through Velocity
        - Highlight "Hot Sellers" that need immediate restocking.
        - Identify slow-moving items from past seasons that are locking up cash flow.

        ### Lineal 2. Size Curve & Inventory Fragmentation Alerts
        - List products with broken size curves (e.g., missing Medium/Large).
        - Provide strategies to clear out remaining fringe sizes (XS/XL).

        ### Faden 3. Quality & Fit Risk Assessment
        - Highlight patterns in customer reviews regarding fabric quality or sizing inconsistencies.
        - Recommend adjustments for future vendor orders.
        """
        try:
            logger.info(f"Generating strategy report using model: {self.model_name}")
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2}
            )
            logger.info("Strategy report generated successfully.")
            return response['message']['content']
        except Exception as e:
            err_msg = f"❌ Ollama Connection Error: {str(e)}. Please verify that `ollama serve` is running."
            logger.error(err_msg)
            return err_msg
