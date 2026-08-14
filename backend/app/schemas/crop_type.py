"""
Crop type enum — must match ml/preprocessing/crop_parameter_ranges.py
exactly, since these are the only crop types the trained model's
OneHotEncoder was fit on. Restricting to an enum (rather than a free
string) means an invalid/unsupported crop is rejected with a clean 422
instead of silently producing a degraded prediction.
"""
from enum import Enum


class CropType(str, Enum):
    RICE = "Rice"
    WHEAT = "Wheat"
    MAIZE = "Maize"
    SOYBEAN = "Soybean"
    SUGARCANE = "Sugarcane"
    COTTON = "Cotton"
