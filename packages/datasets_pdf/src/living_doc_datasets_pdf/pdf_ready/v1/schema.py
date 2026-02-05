# Copyright 2026 AbsaOSS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
PDF Ready v1 JSON Schema export.
"""

import json
from pathlib import Path

from living_doc_datasets_pdf.pdf_ready.v1.models import PdfReadyV1


def export_json_schema(output_path: str | Path | None = None) -> dict:
    """
    Export JSON schema for PdfReadyV1.

    Args:
        output_path: Optional path to write schema file. If None, schema is only returned.

    Returns:
        JSON schema as dictionary.
    """
    schema = PdfReadyV1.model_json_schema()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, sort_keys=True)
            f.write("\n")

    return schema
