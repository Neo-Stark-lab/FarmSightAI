import sys
with open('frontend/src/tests/pages.test.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# For the queued polling test
content = content.replace(
    "await waitFor(() => expect(screen.getByText(/Analysis in progress/i)).toBeInTheDocument());\n      await waitFor(() => expect(apiClient.getAnalysisRun).toHaveBeenCalled(), { timeout: 3000 });",
    "await waitFor(() => expect(screen.getByText(/Analysis in progress/i)).toBeInTheDocument());\n      vi.useFakeTimers();\n      await vi.advanceTimersByTimeAsync(2500);\n      await waitFor(() => expect(apiClient.getAnalysisRun).toHaveBeenCalled());\n      vi.useRealTimers();"
)

# For the failed analysis test
content = content.replace(
    "await waitFor(() => expect(screen.getByText(/Analysis could not be completed/i)).toBeInTheDocument(), { timeout: 3000 });",
    "vi.useFakeTimers();\n      await vi.advanceTimersByTimeAsync(2500);\n      await waitFor(() => expect(screen.getByText(/Analysis could not be completed/i)).toBeInTheDocument());\n      vi.useRealTimers();"
)

with open('frontend/src/tests/pages.test.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
