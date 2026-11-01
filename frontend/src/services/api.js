const API_BASE = '';

export async function fetchHierarchy() {
  const res = await fetch(`${API_BASE}/api/hierarchy`);
  if (!res.ok) throw new Error(`Hierarchy request failed: ${res.status}`);
  return res.json();
}

export async function fetchRegions(market) {
  const res = await fetch(`${API_BASE}/api/hierarchy/regions?market=${encodeURIComponent(market)}`);
  if (!res.ok) throw new Error(`Regions request failed: ${res.status}`);
  return res.json();
}

export async function fetchCountries(region) {
  const res = await fetch(`${API_BASE}/api/hierarchy/countries?region=${encodeURIComponent(region)}`);
  if (!res.ok) throw new Error(`Countries request failed: ${res.status}`);
  return res.json();
}

export async function fetchCategories(department) {
  const res = await fetch(`${API_BASE}/api/hierarchy/categories?department=${encodeURIComponent(department)}`);
  if (!res.ok) throw new Error(`Categories request failed: ${res.status}`);
  return res.json();
}

export async function predictShipping(payload) {
  const res = await fetch(`${API_BASE}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `Prediction failed with status: ${res.status}`);
  }
  return res.json();
}

export async function fetchDashboardData() {
  const res = await fetch(`${API_BASE}/api/dashboard`);
  if (!res.ok) throw new Error(`Dashboard request failed: ${res.status}`);
  return res.json();
}

export async function uploadBatchPrediction(file) {
  const formData = new FormData();
  formData.append('batch_file', file);
  const res = await fetch(`${API_BASE}/api/batch_predict`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `Batch prediction failed with status: ${res.status}`);
  }
  return res.json();
}

export async function fetchCollegeLabsCatalog() {
  const res = await fetch(`${API_BASE}/api/college-labs/catalog`);
  if (!res.ok) throw new Error(`College labs catalog failed: ${res.status}`);
  return res.json();
}

export async function fetchCollegeLab(labId) {
  const res = await fetch(`${API_BASE}/api/college-labs/${labId}`);
  if (!res.ok) throw new Error(`College lab ${labId} request failed: ${res.status}`);
  return res.json();
}

export async function fetchWarehouseSchema() {
  const res = await fetch(`${API_BASE}/api/warehouse/schema`);
  if (!res.ok) throw new Error(`Warehouse schema request failed: ${res.status}`);
  return res.json();
}

export async function fetchWarehouseTable(tableName) {
  const res = await fetch(`${API_BASE}/api/warehouse/table/${encodeURIComponent(tableName)}`);
  if (!res.ok) throw new Error(`Table ${tableName} request failed: ${res.status}`);
  return res.json();
}

