const API_BASE = 'http://localhost:8000/api';

export interface RowData {
    row_index: number;
    data: any;
}

export const fetchSheets = async () => {
    const res = await fetch(`${API_BASE}/sheets`);
    if (!res.ok) throw new Error('Failed to fetch data');
    return res.json();
};

export const previewEmail = async (data: any) => {
    const res = await fetch(`${API_BASE}/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data }),
    });
    if (!res.ok) throw new Error('Failed to generate preview');
    return res.json();
};

export const sendSingle = async (row: RowData) => {
    const res = await fetch(`${API_BASE}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(row),
    });
    if (!res.ok) throw new Error('Failed to send email');
    return res.json();
};

export const draftSingle = async (row: RowData) => {
    const res = await fetch(`${API_BASE}/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(row),
    });
    if (!res.ok) throw new Error('Failed to save draft');
    return res.json();
};


export const uploadCSV = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/upload-csv`, {
        method: 'POST',
        body: formData,
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to upload CSV');
    }
    return res.json();
};
