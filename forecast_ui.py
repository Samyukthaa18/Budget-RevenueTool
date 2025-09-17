import streamlit as st
import pandas as pd
import tempfile
import json
from io import StringIO
from main import logistics_crew

st.set_page_config(page_title="Revenue & Budget Forecast", layout="wide")

st.title("📊 Revenue & Budget Forecast Tool")
st.write("Upload your Excel file with historical revenue/budget data to generate a 12-month forecast.")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    if st.button("▶️ Run Forecast Tool"):
        with st.spinner("Running forecast with Crew..."):
            crew_output = logistics_crew.kickoff(inputs={"file_path": file_path})

            # ✅ Handle CrewOutput correctly
            if hasattr(crew_output, "raw") and crew_output.raw:
                raw_data = crew_output.raw
            elif hasattr(crew_output, "final_output") and crew_output.final_output:
                raw_data = crew_output.final_output
            else:
                st.error("❌ Forecast failed: no data returned from Crew.")
                st.stop()

            try:
                # ✅ If already a dict, convert to DataFrame
                if isinstance(raw_data, dict):
                    df = pd.DataFrame(raw_data)

                # ✅ If string, try JSON first
                elif isinstance(raw_data, str):
                    try:
                        parsed = json.loads(raw_data)
                        df = pd.DataFrame(parsed)
                    except json.JSONDecodeError:
                        # Fallback: treat as JSON string for read_json
                        df = pd.read_json(StringIO(raw_data))

                else:
                    st.error("❌ Forecast data is not in a recognized format.")
                    st.stop()

                # ✅ Rename columns for clarity
                rename_map = {
                    "ds": "Date",
                    "yhat": "Forecast Revenue",
                    "yhat_lower": "Lower Estimate",
                    "yhat_upper": "Upper Estimate"
                }
                df = df.rename(columns=rename_map)

                # ✅ Ensure Date is parsed
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"])

                # ✅ Calculate growth percentages
                if "Forecast Revenue" in df.columns:
                    df = df.sort_values("Date").reset_index(drop=True)

                    # Month-over-month growth (%)
                    df["MoM Growth %"] = df["Forecast Revenue"].pct_change() * 100

                    # Year-over-year growth (%)
                    if len(df) >= 12:
                        first_val = df["Forecast Revenue"].iloc[0]
                        last_val = df["Forecast Revenue"].iloc[-1]
                        yoy_growth = ((last_val - first_val) / first_val) * 100
                    else:
                        yoy_growth = None

                    # 📈 Forecast Summary
                    st.subheader("📈 Forecast Summary")
                    if yoy_growth is not None:
                        st.write(f"**Year-over-Year Growth:** {yoy_growth:.2f}%")
                    else:
                        st.write("Not enough months to calculate YoY growth.")

                # 📅 Forecast Table
                st.subheader("📅 Forecast Table")
                st.dataframe(df, use_container_width=True)

                # 📊 Forecast Chart
                try:
                    import plotly.express as px
                    fig = px.line(df, x="Date", y="Forecast Revenue", title="Revenue Forecast (Next 12 Months)")
                    fig.add_scatter(x=df["Date"], y=df["Lower Estimate"], mode="lines", name="Lower Estimate")
                    fig.add_scatter(x=df["Date"], y=df["Upper Estimate"], mode="lines", name="Upper Estimate")
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.warning("⚠️ Plotly not installed. Run `pip install plotly` for interactive charts.")

            except Exception as e:
                st.error(f"Error displaying forecast: {e}")
