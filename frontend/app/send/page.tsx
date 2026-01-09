'use client';

import { useEffect, useState } from 'react';
import { RowData, fetchSheets, sendSingle, uploadCSV } from '@/lib/api';
import DataTable from '@/components/DataTable';
import Link from 'next/link';
import { ArrowLeft, Send, Loader2, Upload } from 'lucide-react';

export default function SendPage() {
    const [rows, setRows] = useState<RowData[]>([]);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
    const [statusMsg, setStatusMsg] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const res = await fetchSheets();
            setRows(res.rows);
        } catch (e) {
            console.error(e);
            setStatusMsg('Error fetching data');
        } finally {
            setLoading(false);
        }
    };

    const toggleSelect = (index: number) => {
        const next = new Set(selectedIndices);
        if (next.has(index)) next.delete(index);
        else next.add(index);
        setSelectedIndices(next);
    };

    const toggleAll = (selectAll: boolean) => {
        if (selectAll) {
            setSelectedIndices(new Set(rows.map(r => r.row_index)));
        } else {
            setSelectedIndices(new Set());
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setStatusMsg('Uploading CSV...');
        try {
            const res = await uploadCSV(file);
            setRows(res.rows);
            setStatusMsg(`Loaded ${res.count} rows from CSV`);
            setSelectedIndices(new Set());
        } catch (e: any) {
            console.error(e);
            setStatusMsg(`Error uploading CSV: ${e.message}`);
        } finally {
            setUploading(false);
            e.target.value = '';
        }
    };

    const handleSendSelected = async () => {
        if (!confirm(`Are you sure you want to SEND ${selectedIndices.size} emails directly? This cannot be undone.`)) return;

        setProcessing(true);
        setStatusMsg('');
        try {
            const selectedRows = rows.filter(r => selectedIndices.has(r.row_index));
            let successCount = 0;

            for (const row of selectedRows) {
                try {
                    setStatusMsg(`Sending... ${successCount + 1}/${selectedRows.length}`);
                    await sendSingle(row);
                    successCount++;
                } catch (e) {
                    console.error(e);
                }
            }
            setStatusMsg(`Completed! Sent ${successCount} emails.`);
        } catch (e) {
            setStatusMsg('Error during batch process.');
        } finally {
            setProcessing(false);
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center text-green-400"><Loader2 className="animate-spin" size={48} /></div>;

    return (
        <div className="min-h-screen p-8">
            <div className="max-w-7xl mx-auto space-y-6">
                <header className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="p-2 bg-white/5 rounded-full hover:bg-white/10 transition-colors"><ArrowLeft /></Link>
                        <h1 className="text-3xl font-bold text-green-400">Email Send Mode</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-sm text-gray-400">
                            {selectedIndices.size} selected
                        </div>

                        <label className={`cursor-pointer bg-white/10 hover:bg-white/20 text-white border border-white/10 px-4 py-2 rounded font-medium transition-colors flex items-center gap-2 ${processing || uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                            {uploading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
                            <span>Upload CSV</span>
                            <input
                                type="file"
                                accept=".csv"
                                className="hidden"
                                onChange={handleFileUpload}
                                disabled={processing || uploading}
                            />
                        </label>
                        <button
                            onClick={handleSendSelected}
                            disabled={processing || selectedIndices.size === 0}
                            className={`bg-green-600 hover:bg-green-500 text-white shadow-lg shadow-green-500/30 px-4 py-2 rounded font-medium transition-colors flex items-center gap-2 ${processing ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {processing ? <Loader2 className="animate-spin" /> : <Send />}
                            {processing ? 'Sending...' : 'Send Selected'}
                        </button>
                    </div>
                </header>

                {statusMsg && (
                    <div className="p-4 rounded bg-green-500/10 border border-green-500/20 text-green-200">
                        {statusMsg}
                    </div>
                )}

                <div className="glass-panel rounded-xl overflow-hidden border-green-500/20">
                    <DataTable
                        rows={rows}
                        selectedIndices={selectedIndices}
                        onToggleSelect={toggleSelect}
                        onToggleAll={toggleAll}
                    />
                </div>
            </div>
        </div>
    );
}
