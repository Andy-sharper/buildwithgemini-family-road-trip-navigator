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

"""Firestore tools for reading and writing family road trip stops."""

from typing import Any, Optional
from google.cloud import firestore

# Hardcode project ID as a string to avoid project number resolution issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-03-cfff24bedafc"
COLLECTION_NAME = "road_trip_stops"


def _get_firestore_client() -> firestore.Client:
    """Return a Firestore client instance tied to hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def list_road_trip_stops(
    category: Optional[str] = None,
    location: Optional[str] = None,
) -> list[dict[str, Any]]:
    """List and filter family-friendly road trip stops stored in the Firestore database.

    Args:
        category: Optional category filter (e.g., 'Museum', 'Park', 'Aquarium').
        location: Optional location search string (e.g., 'San Francisco', 'Monterey').

    Returns:
        A list of matching stop documents containing name, category, rating, duration, and allergy notes.
    """
    db = _get_firestore_client()
    collection_ref = db.collection(COLLECTION_NAME)
    docs = collection_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        if category and category.lower() not in data.get("category", "").lower():
            continue
        if location and location.lower() not in data.get("location", "").lower():
            continue
        results.append(data)

    return results


def get_road_trip_stop(stop_id: str) -> dict[str, Any]:
    """Retrieve details for a specific road trip stop from Firestore by its ID.

    Args:
        stop_id: The unique ID of the stop (e.g., 'stop_exploratorium_sf').

    Returns:
        Dictionary containing stop details, or error message if not found.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(stop_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return {"error": f"Road trip stop with ID '{stop_id}' not found."}


def add_road_trip_stop(
    stop_id: str,
    name: str,
    location: str,
    category: str,
    kid_friendly_rating: float = 4.5,
    min_age_years: int = 3,
    estimated_duration_mins: int = 90,
    allergy_safe_notes: str = "",
    description: str = "",
) -> str:
    """Save or add a new road trip stop to the Firestore database.

    Args:
        stop_id: Unique identifier for the stop (e.g., 'stop_golden_gate_park').
        name: The display name of the venue or point of interest.
        location: City and state location (e.g., 'San Francisco, CA').
        category: Venue category (e.g., 'Park', 'Museum', 'Restaurant').
        kid_friendly_rating: Rating out of 5 for family friendliness (default: 4.5).
        min_age_years: Recommended minimum age in years.
        estimated_duration_mins: Suggested visit duration in minutes.
        allergy_safe_notes: Notes on food allergy safety, dietary accommodations, or dining rules.
        description: A brief summary of the stop and why it's great for families.

    Returns:
        Confirmation message.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(stop_id)

    stop_data = {
        "stop_id": stop_id,
        "name": name,
        "location": location,
        "category": category,
        "kid_friendly_rating": float(kid_friendly_rating),
        "min_age_years": int(min_age_years),
        "estimated_duration_mins": int(estimated_duration_mins),
        "allergy_safe_notes": allergy_safe_notes,
        "description": description,
    }

    doc_ref.set(stop_data)
    return f"Successfully saved road trip stop '{name}' ({stop_id}) to Firestore database."
