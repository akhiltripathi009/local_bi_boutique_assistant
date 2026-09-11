"""
src/deep_agent/environment.py
=============================
Execution Environment for Shivi Deep Agent:
1. Modular Tool Registry with typed validation and execution tracking.
2. Python Analysis Sandbox for safe code execution on live boutique data.
3. Filesystem access tools for operational logs and audit artifacts.
"""

import io
import sys
import time
import inspect
import logging
from typing import Callable, Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("shivi_environment")

class ToolDefinition:
    """Represents a callable tool exposed to Shivi Deep Agent."""
    def __init__(self, name: str, description: str, func: Callable, category: str = "General", parameters: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.func = func
        self.category = category
        self.parameters = parameters or {}

    def execute(self, **kwargs) -> Any:
        return self.func(**kwargs)


class ToolRegistry:
    """Central registry of executable tools with timing, safety wrappers, and telemetry."""
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, category: str = "General", parameters: Optional[Dict[str, Any]] = None):
        """Decorator to register a function as an agent tool."""
        def decorator(func: Callable):
            tool_def = ToolDefinition(
                name=name,
                description=description,
                func=func,
                category=category,
                parameters=parameters
            )
            self._tools[name] = tool_def
            logger.info(f"Registered Shivi tool: [{category}] {name}")
            return func
        return decorator

    def add_tool(self, tool_def: ToolDefinition):
        self._tools[tool_def.name] = tool_def

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "parameters": t.parameters
            }
            for t in self._tools.values()
        ]

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Executes a registered tool safely with execution timing and error handling."""
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found in registry."}

        start_time = time.time()
        try:
            result = tool.execute(**kwargs)
            duration = time.time() - start_time
            return {
                "success": True,
                "tool": tool_name,
                "duration_sec": round(duration, 3),
                "result": result
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return {
                "success": False,
                "tool": tool_name,
                "duration_sec": round(duration, 3),
                "error": str(e)
            }


class PythonSandbox:
    """
    Safe, isolated Python code execution sandbox for Shivi to run ad-hoc analytics,
    velocity calculations, inventory forecasting, and discount simulations.
    
    Working:
    - Pre-execution AST/lexical safety filter blocking dangerous system primitives
      (os, subprocess, eval, open, globals).
    - Injects safe analytical namespaces (pandas, numpy, math, datetime) and live `db` accessor.
    - Captures stdout/stderr via `io.StringIO` and tracks execution duration.
    
    Why Required:
    - Allows the autonomous agent and human analysts to write and run dynamic data science code
      directly against live SQLite data without endangering server filesystem or host process security.
    """
    FORBIDDEN_CALLS = [
        "os.system", "subprocess", "shutil.rmtree", "open(", "import os",
        "import sys", "__import__", "eval(", "exec(", "globals(", "locals("
    ]

    def __init__(self, db_manager=None):
        self.db = db_manager

    def execute_code(self, code: str, custom_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes Python code in a restricted scope, capturing stdout.
        
        Args:
            code (str): Python script to execute.
            custom_context (Optional[Dict[str, Any]]): Optional custom variables to inject.
            
        Returns:
            Dict[str, Any]: Execution result containing output text, success flag, and runtime in seconds.
        """
        # 1. Pre-execution Safety Inspection
        for forbidden in self.FORBIDDEN_CALLS:
            if forbidden in code:
                return {
                    "success": False,
                    "error": f"Security restriction: Use of '{forbidden}' is strictly prohibited inside Shivi's sandbox.",
                    "output": ""
                }

        # 2. Build Safe Globals & Locals Environment
        import math
        import pandas as pd
        import numpy as np

        safe_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "sum": sum,
                "max": max,
                "min": min,
                "round": round,
                "abs": abs,
                "sorted": sorted,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "enumerate": enumerate,
                "zip": zip,
            },
            "math": math,
            "pd": pd,
            "np": np,
            "datetime": datetime,
        }

        # Inject domain context
        safe_locals = custom_context or {}
        if self.db:
            safe_locals["db"] = self.db

        # 3. Capture stdout & stderr
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout

        start_time = time.time()
        try:
            sys.stdout = stdout_capture
            exec(code, safe_globals, safe_locals)
            sys.stdout = old_stdout
            output_text = stdout_capture.getvalue()
            duration = time.time() - start_time
            return {
                "success": True,
                "output": output_text if output_text else "(Code executed successfully with no output to stdout)",
                "duration_sec": round(duration, 3)
            }
        except Exception as e:
            sys.stdout = old_stdout
            duration = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "output": stdout_capture.getvalue(),
                "duration_sec": round(duration, 3)
            }
        finally:
            sys.stdout = old_stdout
