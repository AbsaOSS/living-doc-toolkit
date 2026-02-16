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
PDF Ready v1 serialization helpers.
"""

import json

from living_doc_datasets_pdf.pdf_ready.v1.models import PdfReadyV1


def to_json(model: PdfReadyV1, indent: int = 2, sort_keys: bool = True) -> str:
    """
    Serialize PdfReadyV1 to JSON string with deterministic output.

    Args:
        model: PdfReadyV1 instance to serialize.
        indent: Indentation level (default: 2).
        sort_keys: Whether to sort keys (default: True).

    Returns:
        JSON string.
    """
    return json.dumps(model.model_dump(mode="json"), indent=indent, sort_keys=sort_keys)


def from_json(json_str: str) -> PdfReadyV1:
    """
    Parse JSON string into PdfReadyV1.

    Args:
        json_str: JSON string to parse.

    Returns:
        PdfReadyV1 instance.
    """
    data = json.loads(json_str)
    return PdfReadyV1.model_validate(data)
