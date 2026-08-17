const API_BASE_URL = 'http://localhost:8000/api/v1/ingestion';

/**
 * Uploads a CSV file to the ingestion pipeline.
 *
 * The backend returns immediately with batch_id + status=PROCESSING.
 * Use pollBatchStatus() or fetchBatchDetails() to track progress.
 *
 * @param {File} file          - The CSV file to upload
 * @param {string} inputType   - SMS | TRANSACTIONS | CUSTOMERS | AUTO_DETECT | etc.
 * @param {string} domainHint  - Optional domain hint (leave empty for auto-detect)
 * @param {number} batchSize   - Records per processing chunk (default 1000)
 */
export async function uploadCSVFile(file, inputType = 'AUTO_DETECT', domainHint = '', batchSize = 1000) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('input_type', inputType);
  formData.append('batch_size', String(batchSize));
  if (domainHint) {
    formData.append('domain_hint', domainHint);
  }

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


/**
 * Fetches all ingestion batch runs (latest 50).
 */
export async function fetchIngestionBatches() {
  const response = await fetch(`${API_BASE_URL}/batches`);
  if (!response.ok) {
    throw new Error('Failed to fetch ingestion batch history');
  }
  return await response.json();
}


/**
 * Fetches a single batch's details including errors.
 * Use this to get live progress while status=PROCESSING.
 *
 * @param {string} batchId
 */
export async function fetchBatchDetails(batchId) {
  const response = await fetch(`${API_BASE_URL}/batches/${batchId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch batch details');
  }
  return await response.json();
}


/**
 * Polls a batch until it is no longer in PROCESSING state.
 *
 * @param {string}   batchId        - The batch to poll
 * @param {Function} onProgress     - Called with the batch object on each poll
 * @param {number}   intervalMs     - Polling interval in ms (default 3000)
 * @param {number}   maxWaitMs      - Max time to wait in ms (default 30 minutes)
 * @returns {Promise<Object>}       - Resolves with the final batch object
 */
export async function pollBatchStatus(batchId, onProgress, intervalMs = 3000, maxWaitMs = 30 * 60 * 1000) {
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const check = async () => {
      try {
        const batch = await fetchBatchDetails(batchId);

        if (onProgress) {
          onProgress(batch);
        }

        if (batch.status === 'PROCESSING' || batch.status === 'PENDING') {
          // Still running — check if we've exceeded max wait
          if (Date.now() - startTime > maxWaitMs) {
            reject(new Error(`Batch ${batchId} did not complete within timeout`));
            return;
          }
          setTimeout(check, intervalMs);
        } else {
          // COMPLETED, FAILED, or PARTIAL — we're done
          resolve(batch);
        }
      } catch (err) {
        reject(err);
      }
    };

    // Start polling after a short initial delay
    setTimeout(check, 1500);
  });
}
