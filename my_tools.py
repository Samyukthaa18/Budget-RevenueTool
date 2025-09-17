# my_tools.py
from crewai_tools import tool
from tools.forecast_tool import run_forecast

@tool("Revenue and Budget Forecast Tool")
def forecast_tool(file_path: str, date_col: str, value_col: str, periods: int = 12) -> str:
    """Generates a revenue/budget forecast from Excel data."""
    results = run_forecast(file_path, date_col, value_col, periods)
    return results.to_string(index=False)
