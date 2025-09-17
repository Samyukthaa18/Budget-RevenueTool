# tools/forecast_tool.py
import pandas as pd
from prophet import Prophet

def run_forecast(file_path: str, date_col: str, value_col: str, periods: int = 12):
    """
    Run a revenue/budget forecast using Prophet.
    file_path: path to Excel file
    date_col: column with dates
    value_col: column with revenue/budget values
    periods: how many future periods to forecast
    """
    df = pd.read_excel(file_path)

    # Prophet expects columns 'ds' (date) and 'y' (value)
    df = df.rename(columns={date_col: "ds", value_col: "y"})

    model = Prophet()
    model.fit(df)

    future = model.make_future_dataframe(periods=periods, freq="M")  # monthly forecast
    forecast = model.predict(future)

    # Return last few forecasted points
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
