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

"""Script to create a Serverless Vertex AI RAG Corpus for Culpeper Complete Herbal."""

import time
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-cfff24bedafc"
LOCATION = "us-central1"  # Serverless RAG mode is us-central1 only
GCS_PATH = "gs://family-road-trip-assets-qwiklabs-gcp-03-cfff24bedafc/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, medicinal uses, plant descriptions, and recipes described in this text. "
    "Ignore and omit all metadata, license boilerplate, and headers. "
    "Output clean, self-contained prose."
)


def create_corpus():
    """Create serverless RAG corpus and import/chunk Culpeper Complete Herbal text."""
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 1. Switch region RAG managed DB to serverless mode
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    print("Configuring Serverless RAG Engine mode...")
    rag.update_rag_engine_config(
        rag_engine_config=rag.RagEngineConfig(
            name=cfg,
            rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
        )
    )

    # 2. Create the corpus with text-embedding-005
    print("Creating RAG corpus 'culpeper-herbal-corpus'...")
    corpus = rag.create_corpus(
        display_name="culpeper-herbal-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    corpus_name = corpus.name
    print(f"✓ Created corpus: {corpus_name}")

    # 3. Import + Parse + Chunk + Embed
    print(f"Importing {GCS_PATH} into corpus...")
    resp = rag.import_files(
        corpus_name=corpus_name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.5-flash",
            custom_parsing_prompt=PARSING_PROMPT,
        ),
    )
    print(f"✓ Imported files count: {resp.imported_rag_files_count}")
    return corpus_name


if __name__ == "__main__":
    c_name = create_corpus()
    print("\nSUCCESS! RAG Corpus Resource Name:")
    print(c_name)
