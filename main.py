import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
from crewai.tools import BaseTool

# --- LLM Configuration ---
llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0.1,
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", "").strip()
)

# --- Forecast Tool ---
class ForecastTool(BaseTool):
    name: str = "RevenueForecastTool"
    description: str = "Generate a 12-month revenue and budget forecast from an Excel dataset."

    def _run(self, file_path: str) -> str:
        import pandas as pd
        from prophet import Prophet

        try:
            df = pd.read_excel(file_path)
            if "Date" not in df.columns or "Revenue" not in df.columns:
                return '{"error": "Excel must have Date and Revenue columns."}'

            # Prophet expects columns: ds (date), y (value)
            df = df.rename(columns={"Date": "ds", "Revenue": "y"})
            df["ds"] = pd.to_datetime(df["ds"])

            model = Prophet()
            model.fit(df)

            future = model.make_future_dataframe(periods=12, freq="M")
            forecast = model.predict(future)

            result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(12)

            # ✅ Always return valid JSON
            return result.to_json(orient="records", date_format="iso")

        except Exception as e:
            return f'{{"error": "Error in forecasting: {str(e)}"}}'

# Export instance for UI usage
forecast_tool = ForecastTool()

# --- Agent Definitions ---
logistics_analyst = Agent(
    role="Senior Logistics Analyst",
    goal="Analyze logistical challenges and identify the core issues",
    backstory=(
        "With a Ph.D. in Supply Chain Management and over 15 years of experience, "
        "you are a master at dissecting complex logistics problems."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm
)

solution_architect = Agent(
    role="Logistics Solution Architect",
    goal="Design innovative and practical solutions for logistics challenges",
    backstory=(
        "You are a visionary architect blending technology, process optimization, "
        "and strategic thinking. Your solutions are scalable and actionable."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ✅ New agent for financial forecasting
financial_forecaster = Agent(
    role="Financial Forecaster",
    goal="Generate accurate revenue and budget forecasts",
    backstory=(
        "A financial expert specializing in predictive analytics and forecasting models. "
        "You rely on statistical tools to produce reliable projections."
    ),
    tools=[forecast_tool],  # ✅ Attach ForecastTool here
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# --- Task Definitions ---
analysis_task = Task(
    description=(
        "A major e-commerce client is struggling with last-mile delivery. "
        "Delivery times are inconsistent and fuel costs increased by 20%. "
        "Analyze this problem and provide three root causes."
    ),
    expected_output="Bullet points with 3 root causes and explanations.",
    agent=logistics_analyst
)

solution_task = Task(
    description=(
        "Using the analysis, design a solution to reduce delivery times by 15% "
        "and cut fuel costs by 10%. Propose specific actions."
    ),
    expected_output="Actionable strategic plan with clear steps and outcomes.",
    agent=solution_architect
)

# ✅ Forecast task for UI use
forecast_task = Task(
    description="Take the uploaded Excel file and generate a 12-month revenue and budget forecast.",
    expected_output="A 12-row JSON with ds, yhat, yhat_lower, yhat_upper fields.",
    agent=financial_forecaster
)

# --- Crew Definition ---
logistics_crew = Crew(
    agents=[logistics_analyst, solution_architect, financial_forecaster],
    tasks=[analysis_task, solution_task, forecast_task],
    process=Process.sequential,
    verbose=True
)

# --- Run Crew from CLI ---
if __name__ == "__main__":
    print("##################################################")
    print("## Starting the Logistics Analysis Crew...      ##")
    print("##################################################")

    result = logistics_crew.kickoff(inputs={"file_path": "your_file.xlsx"})
    print("\n\n################################################")
    print("## Crew execution finished. Final result:      ##")
    print("################################################\n")
    print(result)
