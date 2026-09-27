"""Shared state — holds the loaded ML model and feature columns.

This avoids circular imports between main.py and the routers.
"""
from __future__ import annotations

_model_state: dict = {}


def get_model():
    return _model_state.get("model")


def get_feature_columns():
    return _model_state.get("feature_columns")


def get_metrics():
    return _model_state.get("metrics", {})


def set_model_state(model, feature_columns, metrics):
    _model_state["model"] = model
    _model_state["feature_columns"] = feature_columns
    _model_state["metrics"] = metrics


def clear_model_state():
    _model_state.clear()
