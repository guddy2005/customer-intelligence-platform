const API_BASE_URL = 'http://localhost:8000/api/v1/ingestion';

export async function uploadCSVFile(file, domainHint = 'AUTO_DETECT') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('domain_hint', domainHint);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || 'Upload request failed');
  }

  return await response.json();
}

export async function fetchIngestionBatches() {
  const response = await fetch(`${API_BASE_URL}/batches`);
  if (!response.ok) {
    throw new Error('Failed to fetch ingestion batch history');
  }
  return await response.json();
}

export async function fetchBatchDetails(batchId) {
  const response = await fetch(`${API_BASE_URL}/batches/${batchId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch batch details');
  }
  return await response.json();
}
