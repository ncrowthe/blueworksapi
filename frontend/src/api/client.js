// Base fetch helper
async function apiFetch(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res;
}

export async function fetchMetadataFields() {
  const res = await apiFetch("/api/metadata-fields");
  return res.json();
}

export async function searchProcesses(query, mandatoryFields = []) {
  const res = await apiFetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mandatory_fields: mandatoryFields }),
  });
  return res.json();
}

export async function fetchGlossary() {
  const res = await apiFetch("/api/glossary");
  return res.json();
}

export async function downloadDiagram(processId) {
  const res = await apiFetch(`/api/diagram/${processId}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `diagram-${processId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}
