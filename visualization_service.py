from __future__ import annotations
import pandas as pd

from properties_service import load_properties_from_disk

"""
Handles backend functionality related to generating the map visualization
"""

def get_map_dataframe() -> pd.DataFrame:
    """
    Convert properties directly to a DataFrame for st.map.

    :return: DataFrame
    """
    props = load_properties_from_disk()
    if not props:
        return pd.DataFrame(columns=["lat", "lon"])
    return pd.DataFrame(props)[
        ["lat", "lon", "property_id", "location", "type", "nightly_price", "capacity"]
    ]