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

"""Tools for saving social media points of interest (TikTok/IG/YouTube) and checking route proximity."""

import re
from typing import Any, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-cfff24bedafc"
COLLECTION_NAME = "road_trip_stops"


def _get_db():
    return firestore.Client(project=PROJECT_ID)


def add_social_media_poi(
    name: str,
    location: str,
    source_platform: str = "TikTok",
    notes: str = "",
    category: str = "Social Media Spot",
    post_url: str = "",
    kid_friendly_rating: float = 4.8,
    estimated_duration_mins: int = 60,
    allergy_safe_notes: str = "",
) -> str:
    """Save a point of interest found on TikTok, Instagram, YouTube, or Pinterest to Firestore for route planning.

    Args:
        name: Name or description of the spot (e.g. 'Shark Fin Cove Secret Beach', 'Pie Ranch Fruit Stand').
        location: City, highway mile marker, or area (e.g. 'Davenport, CA', 'San Cruz County, CA').
        source_platform: Where you found it (e.g. 'TikTok', 'Instagram Reel', 'YouTube', 'Pinterest').
        notes: What looked cool or why you want to visit (e.g. 'Saw amazing viral video of sea cave at sunset').
        category: Category of the spot (e.g. 'Beach', 'Scenic View', 'Food Stop', 'Secret Spot').
        post_url: Optional URL or link to the social media post.
        kid_friendly_rating: Family friendliness rating out of 5 (default: 4.8).
        estimated_duration_mins: Suggested visit duration in minutes (default: 60).
        allergy_safe_notes: Notes on food/allergy safety or bringing your own snacks.

    Returns:
        Confirmation message with stop ID.
    """
    db = _get_db()
    # Generate clean stop ID
    clean_slug = re.sub(r"[^a-z0-9_]+", "_", name.lower().strip())
    stop_id = f"social_{clean_slug}"[:40]

    doc_data = {
        "stop_id": stop_id,
        "name": name,
        "location": location,
        "category": category,
        "source_platform": source_platform,
        "social_notes": notes,
        "post_url": post_url,
        "kid_friendly_rating": float(kid_friendly_rating),
        "min_age_years": 2,
        "estimated_duration_mins": int(estimated_duration_mins),
        "allergy_safe_notes": allergy_safe_notes or "Bring allergen-safe snacks for family.",
        "description": f"Discovered on {source_platform}: {notes if notes else name}",
        "is_social_media_pick": True,
    }

    db.collection(COLLECTION_NAME).document(stop_id).set(doc_data)
    return (
        f"✓ Saved social media spot '{name}' ({location}) from {source_platform} to your trip database! "
        f"Stop ID: {stop_id}."
    )


def find_pois_near_route(
    origin: str,
    destination: str,
    max_detour_mins: int = 30,
) -> list[dict[str, Any]]:
    """Check all saved points of interest in Firestore to see which ones are close to the planned route corridor.

    Args:
        origin: Starting point of the route (e.g. 'San Francisco, CA').
        destination: End point of the route (e.g. 'Monterey, CA').
        max_detour_mins: Maximum acceptable detour time in minutes (default: 30).

    Returns:
        List of saved spots that fall along or near the route corridor between origin and destination.
    """
    db = _get_db()
    docs = db.collection(COLLECTION_NAME).stream()

    # Corridor keywords extraction for simple spatial matching
    origin_words = set(re.findall(r"\w+", origin.lower()))
    dest_words = set(re.findall(r"\w+", destination.lower()))

    # Known Northern/Central CA coastal corridor hubs for demo spatial routing
    coastal_hubs = ["san francisco", "pacifica", "half moon bay", "pigeon point", "davenport", "santa cruz", "monterey", "carmel", "big sur"]

    matching_stops = []
    for doc in docs:
        data = doc.to_dict()
        loc = data.get("location", "").lower()

        # Check if spot location overlaps origin, destination, or known corridor cities
        is_near = False
        if any(word in loc for word in origin_words if len(word) > 3):
            is_near = True
        elif any(word in loc for word in dest_words if len(word) > 3):
            is_near = True
        elif any(hub in loc for hub in coastal_hubs if hub in origin.lower() or hub in destination.lower() or "ca" in loc):
            is_near = True

        if is_near:
            # Estimate detour time relative to highway route
            est_detour = 10 if "secret" in data.get("name", "").lower() or "cove" in data.get("name", "").lower() else 5
            data["est_detour_mins"] = est_detour
            data["recommended_action"] = f"Add as a {est_detour}-min stop along {origin} ➔ {destination}"
            matching_stops.append(data)

    return matching_stops
