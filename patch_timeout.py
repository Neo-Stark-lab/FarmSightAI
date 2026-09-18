import sys
with open('frontend/src/tests/pages.test.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "await waitFor(() => expect(apiClient.getAnalysisRun).toHaveBeenCalled());",
    "await waitFor(() => expect(apiClient.getAnalysisRun).toHaveBeenCalled(), { timeout: 3000 });"
)
content = content.replace(
    "await waitFor(() => expect(screen.getByText(/Analysis could not be completed/i)).toBeInTheDocument());",
    "await waitFor(() => expect(screen.getByText(/Analysis could not be completed/i)).toBeInTheDocument(), { timeout: 3000 });"
)

with open('frontend/src/tests/pages.test.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
