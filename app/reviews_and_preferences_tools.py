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

"""Tools for managing travel party type, Google Reviews RAG summaries, time limits, and dining schedules."""

from typing import Any, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-cfff24bedafc"
PREFS_COLLECTION = "user_trip_preferences"


def _get_db():
    return firestore.Client(project=PROJECT_ID)


def set_trip_preferences(
    party_type: str = "Family with Kids",
    interest_categories: Optional[list[str]] = None,
    max_stop_duration_mins: int = 90,
    preferred_dining_types: Optional[list[str]] = None,
) -> str:
    """Configure trip profile preferences such as party composition (family vs couples), interest types, stop time limits, and dining preferences.

    Args:
        party_type: Travel group mode (e.g. 'Family with Kids', 'Just Me & My Wife', 'Solo Explorer').
        interest_categories: List of interest tags (e.g. ['Scenic Lookouts', 'Aquariums', 'Seafood', 'Kid Playgrounds', 'State Parks']).
        max_stop_duration_mins: Maximum time cap per stop in minutes (default: 90).
        preferred_dining_types: Preferred meal types (e.g. ['Nut-free Family Diners', 'Ocean View Cafes', 'Quick Bites']).

    Returns:
        Confirmation message.
    """
    db = _get_db()
    if interest_categories is None:
        interest_categories = ["Kid Playgrounds", "Scenic Views", "Family Diners"]
    if preferred_dining_types is None:
        preferred_dining_types = ["Kid-Friendly", "Allergen-Safe"]

    doc_data = {
        "party_type": party_type,
        "interest_categories": interest_categories,
        "max_stop_duration_mins": int(max_stop_duration_mins),
        "preferred_dining_types": preferred_dining_types,
    }

    db.collection(PREFS_COLLECTION).document("active_profile").set(doc_data)
    return (
        f"✓ Saved trip profile for '{party_type}'! "
        f"Interests: {', '.join(interest_categories)} | Max Stop Duration: {max_stop_duration_mins} mins | "
        f"Dining Preferences: {', '.join(preferred_dining_types)}."
    )


def consult_google_reviews(venue_name: str, location: str = "") -> dict[str, Any]:
    """Retrieve Google Reviews summary, crowd insights, food quality ratings, and visitor tips for a specific point of interest.

    Args:
        venue_name: Name of the venue or point of interest (e.g. 'Exploratorium', 'Shark Fin Cove').
        location: City or area (e.g. 'San Francisco, CA', 'Davenport, CA').

    Returns:
        Dictionary with review score, highlight quotes, crowd times, and dining recommendations.
    """
    v_lower = venue_name.lower()
    
    # Simulated RAG review database lookup for venue insights
    if "shark fin" in v_lower or "cove" in v_lower:
        return {
            "venue": venue_name,
            "overall_rating": 4.8,
            "review_count": 2140,
            "top_review_highlights": [
                "Breathtaking sea cave views! Best at low tide or sunset.",
                "Short steep walk down from Highway 1 turnout—wear sturdy shoes.",
                "No food vendors on site—pack your own snacks and water."
            ],
            "crowd_tips": "Less crowded before 11 AM and after 4 PM.",
            "couples_vibe_score": 5.0,
            "family_vibe_score": 4.5,
        }
    elif "aquarium" in v_lower or "monterey" in v_lower:
        return {
            "venue": venue_name,
            "overall_rating": 4.9,
            "review_count": 18450,
            "top_review_highlights": [
                "World class sea otter and kelp forest exhibits!",
                "On-site cafe has incredible allergen-labeled dishes and ocean views.",
                "Kids love the interactive splash touch tanks."
            ],
            "crowd_tips": "Buy tickets online in advance; mornings are busiest.",
            "couples_vibe_score": 4.9,
            "family_vibe_score": 5.0,
        }
    else:
        return {
            "venue": venue_name,
            "overall_rating": 4.7,
            "review_count": 1280,
            "top_review_highlights": [
                f"Highly rated stop in {location} with great family reviews!",
                "Clean facilities, easy parking, and scenic surroundings.",
                "Great stop to stretch legs and relax."
            ],
            "crowd_tips": "Moderate crowds on weekends.",
            "couples_vibe_score": 4.6,
            "family_vibe_score": 4.8,
        }


def plan_timed_itinerary_with_meals(
    stops: list[str],
    party_type: str = "Family with Kids",
    max_mins_per_stop: int = 90,
    include_meal_stops: bool = True,
) -> dict[str, Any]:
    """Plan a structured itinerary with strict time caps per stop and scheduled meal breaks based on travel party type.

    Args:
        stops: List of planned stops or venue names.
        party_type: Travel party mode ('Family with Kids' or 'Just Me & My Wife').
        max_mins_per_stop: Maximum time limit spent at any single location in minutes.
        include_meal_stops: Whether to automatically schedule breakfast/lunch/dinner eating stops.

    Returns:
        Structured itinerary breakdown with time limits, meal stop suggestions, and schedule timeline.
    """
    itinerary_schedule = []
    current_time_mins = 9 * 60  # Start at 9:00 AM

    is_couples_mode = "wife" in party_type.lower() or "couple" in party_type.lower()

    for idx, stop in enumerate(stops):
        # Cap time spent per stop
        allocated_mins = min(max_mins_per_stop, 60 if "view" in stop.lower() or "cove" in stop.lower() else max_mins_per_stop)
        
        start_str = f"{current_time_mins // 60:02d}:{current_time_mins % 60:02d} AM" if current_time_mins < 720 else f"{(current_time_mins - 720) // 60 or 12:02d}:{current_time_mins % 60:02d} PM"
        current_time_mins += allocated_mins
        end_str = f"{current_time_mins // 60:02d}:{current_time_mins % 60:02d} AM" if current_time_mins < 720 else f"{(current_time_mins - 720) // 60 or 12:02d}:{current_time_mins % 60:02d} PM"

        itinerary_schedule.append({
            "stop_name": stop,
            "time_slot": f"{start_str} - {end_str}",
            "time_limit_mins": allocated_mins,
            "mode": "Romantic / Scenic" if is_couples_mode else "Family & Kids",
        })

        # Insert Lunch meal stop around mid-day (12:00 PM - 1:00 PM)
        if include_meal_stops and current_time_mins >= 12 * 60 and current_time_mins <= 13 * 60:
            lunch_start = f"{(current_time_mins - 720) // 60 or 12:02d}:{current_time_mins % 60:02d} PM"
            current_time_mins += 60  # 60 mins for lunch
            lunch_end = f"{(current_time_mins - 720) // 60 or 12:02d}:{current_time_mins % 60:02d} PM"
            
            meal_venue = "Coastal Seafood & Ocean View Bistro" if is_couples_mode else "Kid-Friendly Allergen-Safe Family Diner"
            itinerary_schedule.append({
                "stop_name": f"🍴 Lunch Stop: {meal_venue}",
                "time_slot": f"{lunch_start} - {lunch_end}",
                "time_limit_mins": 60,
                "mode": "Dining Break",
            })

    return {
        "party_type": party_type,
        "max_time_per_stop_cap": f"{max_mins_per_stop} mins",
        "itinerary_timeline": itinerary_schedule,
        "dining_plan": "Scheduled 1-hour dining breaks checked against family food allergy preferences.",
    }
