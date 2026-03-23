/** Fetch and cache dashboard_data.json */
let _cache = null;

export async function loadData() {
  if (_cache) return _cache;

  const res = await fetch('/data/dashboard_data.json');
  if (!res.ok) throw new Error(`Failed to load data: ${res.status}`);

  _cache = await res.json();
  return _cache;
}

/** Get a subset of data */
export function getData() {
  return _cache;
}
