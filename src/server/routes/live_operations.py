"""
src/server/routes/live_operations.py
====================================
FastAPI router for Segment 2: Live Store & Shop Operations Pipeline.
Provides real-time discrete event simulation control, transactional streaming,
inventory synchronization, and SSE telemetry feeds for the Atelier Web SPA.
"""

import time
import json
import asyncio
import threading
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from starlette.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.data.db_manager import DatabaseManager
from src.simulation.engine import SimulationEngine
from src.core.catalog import CATALOG, generate_initial_inventory

logger = logging.getLogger("live_operations_router")

router = APIRouter(prefix="/api/live-ops", tags=["Live Shop Operations"])

class LiveSettingsRequest(BaseModel):
    promo_discount: Optional[int] = Field(None, ge=0, le=50, description="Promotional flash markdown percentage (0-50%)")
    tick_speed: Optional[float] = Field(None, ge=0.1, le=3.0, description="Simulation tick frequency in seconds")

class LiveOpsManager:
    """Thread-safe singleton managing the live store operations background simulation."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LiveOpsManager, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self.db = DatabaseManager()
        self.sim = SimulationEngine(CATALOG, self.db)
        self.running = False
        self.tick_speed = 0.35
        self.promo_discount = 0
        self.frame_counter = 0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()

        # Initialize inventory from SQLite or catalog fallback
        try:
            db_inv = self.db.get_current_stock_on_hand()
            if db_inv and len(db_inv) == len(CATALOG):
                self.live_inventory = dict(db_inv)
            else:
                self.live_inventory = generate_initial_inventory()
        except Exception as e:
            logger.error(f"Error initializing live ops inventory: {e}")
            self.live_inventory = generate_initial_inventory()

        self.latest_event = {
            "event_text": "Live operations pipeline in standby mode.",
            "event_type": "Idle",
            "product_id": None,
            "product_name": None,
            "unit_price": 0.0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns instantaneous snapshot of the simulation pipeline."""
        with self._state_lock:
            total_revenue = self.db.get_total_historical_revenue()
            low_stock_count = sum(1 for v in self.live_inventory.values() if v <= 15)
            first_pid = next(iter(CATALOG.keys())) if CATALOG else None
            active_pid = self.latest_event.get("product_id") or first_pid

            curr_stock = self.live_inventory.get(active_pid, 50) if active_pid else 50
            circuit_controls = self.db.get_all_circuit_controls()
            max_stock = circuit_controls.get(active_pid, {}).get("max_stock", 100) if active_pid else 100

            return {
                "success": True,
                "running": self.running,
                "tick_speed": self.tick_speed,
                "promo_discount": self.promo_discount,
                "frame_counter": self.frame_counter,
                "total_revenue": total_revenue,
                "low_stock_count": low_stock_count,
                "total_shop_units": sum(self.live_inventory.values()),
                "latest_event": dict(self.latest_event),
                "active_product_context": {
                    "product_id": active_pid,
                    "product_name": CATALOG.get(active_pid, {}).get("name", "Boutique Apparel") if active_pid else "Boutique Apparel",
                    "current_stock": curr_stock,
                    "max_stock": max_stock,
                    "unit_price": CATALOG.get(active_pid, {}).get("price", 0.0) if active_pid else 0.0
                }
            }

    def execute_tick(self) -> Dict[str, Any]:
        """Executes a single discrete simulation tick."""
        with self._state_lock:
            self.frame_counter += 1
            event_text, event_type, event_pid = self.sim.process_tick(self.promo_discount, self.live_inventory)

            p_name = CATALOG.get(event_pid, {}).get("name", "") if event_pid else ""
            u_price = CATALOG.get(event_pid, {}).get("price", 0.0) if event_pid else 0.0

            self.latest_event = {
                "event_text": event_text,
                "event_type": event_type,
                "product_id": event_pid,
                "product_name": p_name,
                "unit_price": u_price,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            circuit_controls = self.db.get_all_circuit_controls()
            curr_stock = self.live_inventory.get(event_pid, 0) if event_pid else 0
            max_stock = circuit_controls.get(event_pid, {}).get("max_stock", 100) if event_pid else 100

            total_revenue = self.db.get_total_historical_revenue()
            low_stock_count = sum(1 for v in self.live_inventory.values() if v <= 15)

            return {
                "success": True,
                "frame_counter": self.frame_counter,
                "event": dict(self.latest_event),
                "active_stock": curr_stock,
                "max_stock": max_stock,
                "total_revenue": total_revenue,
                "low_stock_count": low_stock_count,
                "inventory_snapshot": dict(self.live_inventory)
            }

    def _simulation_worker(self):
        """Background thread executing ticks while active."""
        logger.info("Live Operations background simulation worker started.")
        while not self._stop_event.is_set():
            try:
                self.execute_tick()
            except Exception as e:
                logger.error(f"Error during simulation tick execution: {e}")
            time.sleep(max(0.1, self.tick_speed))
        logger.info("Live Operations background simulation worker paused.")

    def start(self):
        """Starts background simulation loop."""
        with self._state_lock:
            if self.running:
                return
            self.running = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._simulation_worker, daemon=True)
            self._thread.start()

    def pause(self):
        """Pauses background simulation loop."""
        with self._state_lock:
            if not self.running:
                return
            self.running = False
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                # give short grace to stop
                pass

    def update_settings(self, promo_discount: Optional[int] = None, tick_speed: Optional[float] = None):
        """Updates simulation parameters safely."""
        with self._state_lock:
            if promo_discount is not None:
                self.promo_discount = max(0, min(50, promo_discount))
            if tick_speed is not None:
                self.tick_speed = max(0.1, min(3.0, tick_speed))

    def reset_inventory(self):
        """Synchronizes live memory inventory with the SQLite database."""
        with self._state_lock:
            db_inv = self.db.get_current_stock_on_hand()
            if db_inv:
                self.live_inventory = dict(db_inv)
            else:
                self.live_inventory = generate_initial_inventory()
            self.latest_event = {
                "event_text": "Live inventory re-synchronized with SQLite database.",
                "event_type": "Idle",
                "product_id": None,
                "product_name": None,
                "unit_price": 0.0,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def get_stock_chart_data(self) -> List[Dict[str, Any]]:
        """Returns categorized product inventory for dynamic visual chart highlighting."""
        with self._state_lock:
            active_pid = self.latest_event.get("product_id")
            event_type = self.latest_event.get("event_type", "Idle")

            chart_items = []
            for pid, details in CATALOG.items():
                stock = self.live_inventory.get(pid, 0)
                # Dynamic event color taxonomy
                if pid == active_pid:
                    if event_type == "Purchase":
                        color = "#10b981"  # Emerald Restock
                        tag = "RESTOCKED"
                    elif event_type == "Sale":
                        color = "#f59e0b"  # Amber Sale
                        tag = "PURCHASED"
                    else:
                        color = "#6366f1"  # Indigo Event
                        tag = "ACTIVE"
                elif stock <= 15:
                    color = "#ef4444"      # Safety stock breach (Crimson)
                    tag = "LOW SAFETY"
                else:
                    color = "#1e293b"      # Stable baseline (Slate)
                    tag = "STABLE"

                chart_items.append({
                    "product_id": pid,
                    "product_name": details["name"],
                    "category": details.get("category", "Couture"),
                    "price": details.get("price", 0.0),
                    "stock": stock,
                    "color": color,
                    "tag": tag,
                    "is_active_target": (pid == active_pid)
                })

            return chart_items

    def get_ledgers(self, limit: int = 8) -> Dict[str, Any]:
        """Fetches the latest real-time sales and procurement log entries."""
        sales_df = self.db.fetch_logs("sales_ledger", limit=limit)
        purchases_df = self.db.fetch_logs("purchase_ledger", limit=limit)

        sales = []
        if not sales_df.empty:
            for _, r in sales_df.iterrows():
                sales.append({
                    "timestamp": str(r.get("timestamp", "")),
                    "product_name": str(r.get("product_name", "")),
                    "revenue": float(r.get("total_revenue", 0.0)),
                    "customer_name": str(r.get("customer_name", "VIP Client")),
                    "size_purchased": str(r.get("size_purchased", "M")),
                    "is_promotional": bool(r.get("is_promotional", 0))
                })

        purchases = []
        if not purchases_df.empty:
            for _, r in purchases_df.iterrows():
                purchases.append({
                    "timestamp": str(r.get("timestamp", "")),
                    "product_name": str(r.get("product_name", "")),
                    "quantity": int(r.get("quantity", 0)),
                    "cost": float(r.get("total_cost", 0.0))
                })

        return {
            "success": True,
            "sales_log": sales,
            "restocks_log": purchases
        }

# Global singleton instance
ops_manager = LiveOpsManager()

@router.get("/status")
def get_live_ops_status() -> Dict[str, Any]:
    """Returns current operational status, simulation parameters, and active product state."""
    return ops_manager.get_status()

@router.post("/start")
def start_live_ops() -> Dict[str, Any]:
    """Activates the continuous discrete-event retail simulation loop."""
    ops_manager.start()
    return {"success": True, "message": "Live Store Operations loop activated.", "running": True}

@router.post("/pause")
def pause_live_ops() -> Dict[str, Any]:
    """Pauses the continuous retail simulation loop in clean standby mode."""
    ops_manager.pause()
    return {"success": True, "message": "Live Store Operations loop paused.", "running": False}

@router.post("/tick")
def step_simulation_tick() -> Dict[str, Any]:
    """Manually steps a single discrete simulation cycle."""
    return ops_manager.execute_tick()

@router.post("/settings")
def update_live_ops_settings(payload: LiveSettingsRequest) -> Dict[str, Any]:
    """Updates promotional flash markdown % and tick frequency."""
    ops_manager.update_settings(
        promo_discount=payload.promo_discount,
        tick_speed=payload.tick_speed
    )
    return {
        "success": True,
        "promo_discount": ops_manager.promo_discount,
        "tick_speed": ops_manager.tick_speed
    }

@router.post("/reset")
def reset_live_ops_inventory() -> Dict[str, Any]:
    """Re-synchronizes in-memory stock balances from SQLite persistent storage."""
    ops_manager.reset_inventory()
    return {"success": True, "message": "Live inventory re-synchronized with SQLite database."}

@router.get("/stock-chart")
def get_stock_chart() -> Dict[str, Any]:
    """Returns product stock levels with dynamic event color tagging."""
    return {
        "success": True,
        "items": ops_manager.get_stock_chart_data(),
        "latest_event": ops_manager.latest_event
    }

@router.get("/logs")
def get_live_ledgers(limit: int = Query(8, ge=1, le=50)) -> Dict[str, Any]:
    """Returns the most recent customer sales and inbound delivery logs."""
    return ops_manager.get_ledgers(limit=limit)

@router.get("/stream")
async def live_telemetry_stream():
    """
    Server-Sent Events (SSE) telemetry endpoint.
    Emits continuous real-time state and tick snapshots to connected clients.
    """
    async def event_generator():
        last_frame = -1
        while True:
            status = ops_manager.get_status()
            current_frame = status.get("frame_counter", 0)

            # Emit payload if frame advanced or periodic heartbeat
            payload = {
                "status": status,
                "chart": ops_manager.get_stock_chart_data(),
                "ledgers": ops_manager.get_ledgers(limit=6)
            }
            yield f"data: {json.dumps(payload)}\n\n"
            last_frame = current_frame

            sleep_dur = max(0.15, ops_manager.tick_speed if ops_manager.running else 1.0)
            await asyncio.sleep(sleep_dur)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
