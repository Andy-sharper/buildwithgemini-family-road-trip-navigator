# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Route calculation and Google Maps navigation tools for Family Road Trip Navigator."""

from typing import Any, Optional, Union
import urllib.parse


def calculate_driving_route(
    origin: str,
    destination: str,
    stops: Optional[Union[list[str], str]] = None,
    avg_speed_mph: float = 55.0,
    vehicle_mpg: float = 25.0,
    gas_price_per_gal: float = 4.25,
) -> dict[str, Any]:
    """Calculate driving route summary, family rest-stop recommendations, and generate a live Google Maps directions URL.

    Args:
        origin: Starting city or address (e.g., 'San Francisco, CA').
        destination: Final destination city or address (e.g., 'Monterey, CA').
        stops: Optional list or comma-separated string of intermediate stop names or waypoints (e.g., ['Exploratorium', 'Pigeon Point Light Station']).
        avg_speed_mph: Estimated average driving speed in miles per hour (default: 55.0).
        vehicle_mpg: Estimated vehicle fuel efficiency in miles per gallon (default: 25.0).
        gas_price_per_gal: Estimated fuel price per gallon in dollars (default: 4.25).

    Returns:
        Dictionary containing route legs, estimated driving time, fuel cost, family rest stop schedule, and Google Maps URL.
    """
    # Parse stops list
    waypoints_list: list[str] = []
    if isinstance(stops, str):
        waypoints_list = [s.strip() for s in stops.split(",") if s.strip()]
    elif isinstance(stops, list):
        waypoints_list = [str(s).strip() for s in stops if str(s).strip()]

    # Construct Google Maps Directions URL
    base_url = "https://www.google.com/maps/dir/?api=1"
    params = {
        "origin": origin,
        "destination": destination,
    }
    if waypoints_list:
        params["waypoints"] = "|".join(waypoints_list)

    google_maps_url = f"{base_url}&{urllib.parse.urlencode(params)}"

    # Estimate distance & drive time (simulated leg estimation for planning)
    num_legs = len(waypoints_list) + 1
    est_miles_per_leg = 45.0
    total_est_miles = num_legs * est_miles_per_leg
    total_drive_hours = total_est_miles / avg_speed_mph
    total_drive_mins = int(total_drive_hours * 60)

    # Fuel cost estimation
    gallons_needed = total_est_miles / vehicle_mpg
    est_fuel_cost = round(gallons_needed * gas_price_per_gal, 2)

    # Family rest stop schedule (recommend 20-min break every 2 hours of driving for kids)
    recommended_rest_breaks = max(0, int(total_drive_hours // 2))
    rest_break_recommendation = (
        f"For a family with kids, plan {recommended_rest_breaks} rest-stop break(s) "
        f"(15–30 mins each) every 2 hours of driving to stretch legs and grab allergen-safe snacks."
        if recommended_rest_breaks > 0
        else "Short drive (<2 hours)—no major rest breaks required before destination."
    )

    all_points = [origin] + waypoints_list + [destination]
    route_legs_summary = " ➔ ".join(all_points)

    return {
        "origin": origin,
        "destination": destination,
        "waypoints": waypoints_list,
        "route_legs": route_legs_summary,
        "total_est_miles": round(total_est_miles, 1),
        "total_est_drive_time": f"{total_drive_mins // 60}h {total_drive_mins % 60}m",
        "est_fuel_cost_usd": f"${est_fuel_cost:.2f}",
        "family_rest_recommendation": rest_break_recommendation,
        "google_maps_url": google_maps_url,
    }
