from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from src.data.db_manager import DatabaseManager
from src.deep_agent.environment import PythonSandbox

router = APIRouter(prefix="/api/sandbox", tags=["Data Science Sandbox"])

def get_sandbox() -> PythonSandbox:
    db = DatabaseManager()
    return PythonSandbox(db_manager=db)

class ExecuteCodeRequest(BaseModel):
    code: str

PRESETS = {
    "📈 Top 5 Margin Styles": (
        "# Calculate top 5 highest profit styles from sales ledger\n"
        "sales = db.fetch_logs('sales_ledger', limit=100)\n"
        "if not sales.empty:\n"
        "    top = sales.groupby('product_name')['gross_profit'].sum().sort_values(ascending=False).head(5)\n"
        "    print('Top 5 Profit Generating Styles:')\n"
        "    for name, profit in top.items():\n"
        "        print(f'  - {name}: ${profit:,.2f}')\n"
        "else:\n"
        "    print('No sales recorded yet.')"
    ),
    "📦 Days of Inventory Remaining (DOI)": (
        "# Estimate inventory runway based on current stock\n"
        "stock = db.get_current_stock_on_hand()\n"
        "wh = db.get_warehouse_stock_on_hand()\n"
        "print('Total Boutique Inventory Position:')\n"
        "print(f'  - Shop Floor Units: {sum(stock.values()):,}')\n"
        "print(f'  - Warehouse Reserve Units: {sum(wh.values()):,}')\n"
        "print(f'  - Total Enterprise Units: {sum(stock.values()) + sum(wh.values()):,}')"
    ),
    "🎂 Upcoming Birthday VIPs": (
        "# Query upcoming VIP birthdays within next 14 days\n"
        "bdays = db.get_upcoming_birthday_customers(days_ahead=14)\n"
        "print(f'Found {len(bdays)} VIP clients celebrating in next 14 days:')\n"
        "for b in bdays:\n"
        "    print(f'  - {b[\"name\"]} ({b[\"loyalty_tier\"]}): DOB {b[\"dob\"]} (in {b[\"days_until\"]} days)')"
    ),
    "⚠️ Low Stock & Warehouse Restock Need": (
        "# Identify styles on shop floor needing warehouse restocking (<= 15 units)\n"
        "shop_stock = db.get_current_stock_on_hand()\n"
        "wh_stock = db.get_warehouse_stock_on_hand()\n"
        "low_stock = {k: v for k, v in shop_stock.items() if v <= 15}\n"
        "print(f'Shop Styles Requiring Restock (<= 15 units): {len(low_stock)}')\n"
        "if low_stock:\n"
        "    for name, qty in list(low_stock.items())[:5]:\n"
        "        wh_qty = wh_stock.get(name, 0)\n"
        "        print(f'  - {name}: Shop Floor={qty} units | Warehouse Reserve={wh_qty} units')\n"
        "else:\n"
        "    print('All shop floor merchandise is safely stocked above minimum safety levels.')"
    ),
    "👥 VIP Patron Loyalty Tier Breakdown": (
        "# Analyze customer segmentation and lifetime spend by loyalty tier\n"
        "custs = db.get_all_customers()\n"
        "if not custs.empty:\n"
        "    print('VIP Patron Loyalty Tier Breakdown:')\n"
        "    summary = custs.groupby('loyalty_tier').agg(\n"
        "        client_count=('id', 'count'),\n"
        "        avg_spend=('total_spend', 'mean')\n"
        "    ).reset_index()\n"
        "    for _, row in summary.iterrows():\n"
        "        print(f\"  - {row['loyalty_tier']}: {int(row['client_count'])} clients (Avg Spend: ${row['avg_spend']:,.2f})\")\n"
        "else:\n"
        "    print('No customer profiles recorded.')"
    ),
    "🏷️ Active Campaigns & Discount Breakdown": (
        "# Audit live promotional campaigns and discount tiers\n"
        "camps = db.get_all_campaigns()\n"
        "if not camps.empty:\n"
        "    print('Registered Boutique Marketing Campaigns:')\n"
        "    for _, c in camps.iterrows():\n"
        "        status = '🟢 ACTIVE' if c['status'] == 'Active' else '⚪ ' + c['status']\n"
        "        print(f\"  - [{status}] {c['name']} ({c['discount_pct']}% Off) - Category: {c['target_category']}\")\n"
        "else:\n"
        "    print('No promotional campaigns registered.')"
    )
}

@router.get("/presets")
def get_sandbox_presets() -> Dict[str, Any]:
    """Returns the 6 verified boutique analytical scripts."""
    return {
        "success": True,
        "presets": PRESETS
    }

@router.post("/execute")
def execute_sandbox_code(req: ExecuteCodeRequest) -> Dict[str, Any]:
    """Safely executes Python scripts in the isolated data science sandbox."""
    sb = get_sandbox()
    res = sb.execute_code(req.code)
    return res
