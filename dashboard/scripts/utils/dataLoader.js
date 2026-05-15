export async function loadDashboardData() {
    const res = await fetch('./data/dashboard_data.json');
    if (!res.ok) throw new Error('Data file not found');
    return res.json();
}
