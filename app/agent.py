# ruff: noqa
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

import datetime
import json
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import (
    AgentEngineSandboxCodeExecutor,
)
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

AGENT_ENGINE_RESOURCE_NAME = (
    "projects/267352997289/locations/us-east1/reasoningEngines/3856119220005765120"
)

try:
    metadata_path = os.path.join(
        os.path.dirname(__file__), "..", "deployment_metadata.json"
    )
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            data = json.load(f)
            if "remote_agent_runtime_id" in data:
                AGENT_ENGINE_RESOURCE_NAME = data["remote_agent_runtime_id"]
except Exception:
    pass

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME
)

from app.firestore_tools import (
    add_road_trip_stop,
    get_road_trip_stop,
    list_road_trip_stops,
)
from app.image_tools import generate_scenic_road_trip_postcard
from app.rag_tools import consult_herbal_corpus
from app.reviews_and_preferences_tools import (
    consult_google_reviews,
    plan_timed_itinerary_with_meals,
    set_trip_preferences,
)
from app.route_tools import calculate_driving_route
from app.social_poi_tools import add_social_media_poi, find_pois_near_route

MODEL = "gemini-3.6-flash"


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to send completed turn session events to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def record_family_allergy(family_member: str, allergy_details: str) -> str:
    """Record a family member's allergy or dietary restriction so it is remembered for future road trip planning.

    Args:
        family_member: The name or role of the family member (e.g. 'Son (6yo)', 'Dad', 'Mom', 'Daughter').
        allergy_details: Description of the allergy or severe restriction (e.g. 'Severe peanut allergy', 'Gluten intolerance', 'Shellfish allergy').

    Returns:
        Confirmation string confirming the recorded allergy.
    """
    return f"Recorded allergy for {family_member}: {allergy_details}. This will be remembered across sessions to filter out unsafe food stops, snacks, and activities."


from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from app.a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description="Family Road Trip Navigator assistant helping plan family road trips, kid-friendly stops, itineraries, and driving routes.",
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

domain_instruction = (
    "You are a helpful Family Road Trip Navigator assistant. You help plan family road trips "
    "by finding kid-friendly points of interest, saving custom stop itineraries, and organizing driving routes.\n\n"
    "CRITICAL ALLERGY & MEMORY DIRECTIVES:\n"
    "- Actively identify, track, and remember ALL user and family member allergies "
    "(e.g., food allergies like peanut, tree nut, gluten, dairy, egg, shellfish; bee stings; pet dander; environmental/pollen allergies).\n"
    "- When the user mentions an allergy, call `record_family_allergy` to register it.\n"
    "- Store and recall these allergies across sessions so that you NEVER suggest restaurants, snack stops, dining options, "
    "or outdoor activities that violate any family member's allergy or dietary safety requirement.\n"
    "- When recommending food stops or activities, explicitly double-check them against remembered allergies and highlight safe choices."
)

instruction = f"{domain_instruction}\n\n{a2ui_instruction}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        get_weather,
        get_current_time,
        record_family_allergy,
        list_road_trip_stops,
        get_road_trip_stop,
        add_road_trip_stop,
        calculate_driving_route,
        consult_herbal_corpus,
        add_social_media_poi,
        find_pois_near_route,
        set_trip_preferences,
        consult_google_reviews,
        plan_timed_itinerary_with_meals,
        generate_scenic_road_trip_postcard,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    code_executor=code_executor,
)

app = App(
    root_agent=root_agent,
    name="app",
)
