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

"""Import and index Culpeper Herbal file into the created RAG corpus."""

import vertexai
from vertexai.preview import rag

PROJECT_ID = "qwiklabs-gcp-03-cfff24bedafc"
LOCATION = "us-west1"
GCS_PATH = "gs://family-road-trip-assets-qwiklabs-gcp-03-cfff24bedafc/rag/pg49513.txt"
CORPUS_NAME = "projects/267352997289/locations/us-west1/ragCorpora/4611686018427387904"


def import_herbal_file():
    """Import and index file into RAG Corpus using default chunking parser."""
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(f"Importing {GCS_PATH} into corpus {CORPUS_NAME}...")

    resp = rag.import_files(
        corpus_name=CORPUS_NAME,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
    )
    print(f"✓ Successfully imported {resp.imported_rag_files_count} file(s) into RAG corpus!")


if __name__ == "__main__":
    import_herbal_file()
