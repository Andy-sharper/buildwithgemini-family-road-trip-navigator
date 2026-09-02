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

"""RAG retrieval tools for Culpeper Complete Herbal corpus."""

import vertexai
from vertexai.preview import rag

PROJECT_ID = "qwiklabs-gcp-03-cfff24bedafc"
RAG_LOCATION = "us-west1"
CORPUS_NAME = "projects/267352997289/locations/us-west1/ragCorpora/4611686018427387904"


def consult_herbal_corpus(query: str) -> str:
    """Search the Culpeper Complete Herbal RAG corpus for medicinal plants, remedies, and herbal lore.

    Args:
        query: What to look up (a plant, ailment, remedy, or recipe).

    Returns:
        Matched passages from Nicholas Culpeper's Complete Herbal book.
    """
    try:
        vertexai.init(project=PROJECT_ID, location=RAG_LOCATION)
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        if passages:
            return "\n\n---\n\n".join(passages)
        return "No relevant passages found in the Herbal corpus."
    except Exception as e:
        return f"Herbal corpus retrieval notice/status: {e}"
