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

"""Image generation tools for Family Road Trip Navigator using gemini-3.1-flash-lite-image."""

import time
import re
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-03-cfff24bedafc"
BUCKET_NAME = "family-road-trip-assets-qwiklabs-gcp-03-cfff24bedafc"


async def generate_scenic_road_trip_postcard(
    stop_name: str,
    location: str,
    description: str = "",
    tool_context: ToolContext = None,
) -> str:
    """Generate a scenic AI postcard image for a road trip stop using gemini-3.1-flash-lite-image in the global region.

    Saves the image as an artifact in the Playground panel AND uploads the bytes to a public GCS bucket,
    returning its public HTTPS URL.

    Args:
        stop_name: Name of the road trip stop or point of interest (e.g. 'Shark Fin Cove', 'Exploratorium').
        location: City or area (e.g. 'Davenport, CA', 'San Francisco, CA').
        description: Visual details or theme (e.g. 'Sunny coastal sunset view with family on beach').
        tool_context: ADK ToolContext instance provided automatically by ADK runtime.

    Returns:
        Public HTTPS GCS URL of the generated postcard image.
    """
    try:
        # Initialize Gemini client in global region
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

        prompt = (
            f"A vibrant, high-quality scenic postcard for '{stop_name}' located in {location}. "
            f"Style: Modern family road trip souvenir postcard with stylized text '{stop_name}'. "
            f"Visual details: {description if description else 'Beautiful landscape view with bright cheerful colors'}"
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        image_bytes = None
        for candidate in getattr(response, "candidates", []):
            content = getattr(candidate, "content", None)
            if content and getattr(content, "parts", None):
                for part in content.parts:
                    if getattr(part, "inline_data", None) is not None:
                        image_bytes = part.inline_data.data
                        break

        if not image_bytes:
            return "Failed to generate image bytes from model response."

        # Clean filename slug
        slug = re.sub(r"[^a-z0-9_]+", "_", stop_name.lower().strip())
        filename = f"postcard_{slug}_{int(time.time())}.png"

        # (1) Save with tool_context.save_artifact so it shows in Playground's Artifacts panel
        if tool_context is not None:
            part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            await tool_context.save_artifact(filename=filename, artifact=part)

        # (2) Upload the same image bytes directly to the public GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url

    except Exception as e:
        return f"Error generating or saving image: {str(e)}"
