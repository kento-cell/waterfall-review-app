from __future__ import annotations

import json


class StubLLMClient:
    async def review_artifact(self, prompt: str) -> str:
        return json.dumps(
            [
                {
                    "location": "Line:1",
                    "severity": "high",
                    "content": "Stub high severity finding",
                    "suggestion": "Review and fix the high severity issue.",
                },
                {
                    "location": "Line:2",
                    "severity": "mid",
                    "content": "Stub mid severity finding",
                    "suggestion": "Review and fix the mid severity issue.",
                },
            ],
            ensure_ascii=False,
        )
