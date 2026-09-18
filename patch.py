import sys
with open('frontend/src/tests/pages.test.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "{ status: 'insufficient_data', risk_level: 'unknown', probability: null, confidence: { level: 'low', basis: [] } }",
    "{ status: 'insufficient_data', prediction_type: 'water_stress', risk_level: 'unknown', probability: null, confidence: { level: 'low', basis: [] } }"
)

with open('frontend/src/tests/pages.test.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
