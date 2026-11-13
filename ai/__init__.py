"""
AI & Predictive Analytics Package for LabStock AI.
Includes starter models for time-series demand forecasting and consumption anomaly detection.
"""

from .forecasting import DemandForecaster
from .anomaly_detection import InventoryAnomalyDetector

__all__ = ['DemandForecaster', 'InventoryAnomalyDetector']
