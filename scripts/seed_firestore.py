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

"""Seed script for Family Road Trip Navigator Firestore collection."""

from google.cloud import firestore

# Hardcode project ID as a string to avoid project number resolution issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-03-cfff24bedafc"
COLLECTION_NAME = "road_trip_stops"

SEEDED_STOPS = [
    {
        "stop_id": "stop_exploratorium_sf",
        "name": "Exploratorium",
        "location": "San Francisco, CA",
        "category": "Museum",
        "kid_friendly_rating": 4.9,
        "min_age_years": 3,
        "estimated_duration_mins": 120,
        "allergy_safe_notes": "Nut-free cafeteria options, clear allergen labeling at dining kiosks.",
        "description": "Interactive museum of science, art, and human perception right on Pier 15.",
    },
    {
        "stop_id": "stop_presidio_tunnel_tops",
        "name": "Presidio Tunnel Tops & Outpost Play Area",
        "location": "San Francisco, CA",
        "category": "Park",
        "kid_friendly_rating": 4.8,
        "min_age_years": 2,
        "estimated_duration_mins": 90,
        "allergy_safe_notes": "Outdoor picnic tables. Great for bringing your own allergen-safe snacks.",
        "description": "Vast green space with views of the Golden Gate Bridge and a natural wooden playground.",
    },
    {
        "stop_id": "stop_cal_academy_sciences",
        "name": "California Academy of Sciences",
        "location": "San Francisco, CA",
        "category": "Museum / Aquarium",
        "kid_friendly_rating": 4.9,
        "min_age_years": 4,
        "estimated_duration_mins": 150,
        "allergy_safe_notes": "Academy Cafe offers gluten-free and nut-free packaged meals.",
        "description": "Natural history museum, aquarium, 4-story living rainforest, and planetarium under one living roof.",
    },
    {
        "stop_id": "stop_monterey_bay_aquarium",
        "name": "Monterey Bay Aquarium",
        "location": "Monterey, CA",
        "category": "Aquarium",
        "kid_friendly_rating": 5.0,
        "min_age_years": 2,
        "estimated_duration_mins": 180,
        "allergy_safe_notes": "Cafeteria lists top-8 allergen info for all prepared dishes.",
        "description": "World-famous ocean habitat with sea otters, kelp forest exhibits, and interactive touch pools.",
    },
    {
        "stop_id": "stop_dinosaur_land_park",
        "name": "Dinosaur & Fossil Discovery Park",
        "location": "Santa Cruz, CA",
        "category": "Theme / Educational Park",
        "kid_friendly_rating": 4.7,
        "min_age_years": 3,
        "estimated_duration_mins": 90,
        "allergy_safe_notes": "Peanut-free snack bar. Pre-packaged allergen-friendly ice pop treats available.",
        "description": "Life-sized animatronic dinosaur exhibits, fossil dig sandpits, and interactive paleontologist talks.",
    },
]


def seed_database():
    """Seed initial road trip stop documents into Firestore."""
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)

    print(f"Seeding '{COLLECTION_NAME}' collection in project '{PROJECT_ID}'...")
    for stop in SEEDED_STOPS:
        doc_ref = collection_ref.document(stop["stop_id"])
        doc_ref.set(stop)
        print(f"  ✓ Seeded: {stop['name']} ({stop['stop_id']})")

    print(f"Successfully seeded {len(SEEDED_STOPS)} road trip stops!")


if __name__ == "__main__":
    seed_database()
