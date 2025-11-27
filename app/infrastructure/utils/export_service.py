import csv
import io
from typing import List
from ...application.domain.entities import ForecastData, Metrics

class ExportService:
    @staticmethod
    def export_forecast_to_csv(forecast_data: List[ForecastData], metrics: Metrics) -> str:
        """Export forecast data and metrics to CSV format"""
        output = io.StringIO()

        # Write metrics section
        writer = csv.writer(output)
        writer.writerow(["Demand Forecasting Report"])
        writer.writerow([])
        writer.writerow(["Metrics"])
        writer.writerow(["MAE", metrics.mae])
        writer.writerow(["RMSE", metrics.rmse])
        writer.writerow(["Demand Trend (%)", metrics.demand_trend])
        writer.writerow(["Volatility Score", metrics.volatility_score])
        writer.writerow([])

        # Write forecast data section
        writer.writerow(["Forecast Data"])
        writer.writerow(["Month", "Actual Demand", "Predicted Demand"])

        for data in forecast_data:
            writer.writerow([
                data.month,
                data.actual if data.actual is not None else "",
                data.predicted
            ])

        return output.getvalue()

    @staticmethod
    def export_forecast_to_json(forecast_data: List[ForecastData], metrics: Metrics) -> dict:
        """Export forecast data and metrics to JSON format"""
        return {
            "metrics": {
                "mae": metrics.mae,
                "rmse": metrics.rmse,
                "demand_trend": metrics.demand_trend,
                "volatility_score": metrics.volatility_score
            },
            "forecast_data": [
                {
                    "month": data.month,
                    "actual": data.actual,
                    "predicted": data.predicted
                }
                for data in forecast_data
            ]
        }