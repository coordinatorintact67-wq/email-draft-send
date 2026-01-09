'use client';

import { useEffect, useState } from 'react';
import { RowData, fetchSheets, draftSingle } from '@/lib/api';
import DataTable from '@/components/DataTable';
import Link from 'next/link';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';

export default function DraftPage() {
    const [rows, setRows] = useState<RowData[]>([]);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
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

    const handleDraftSelected = async () => {
        setProcessing(true);
        setStatusMsg('');
        try {
            const selectedRows = rows.filter(r => selectedIndices.has(r.row_index));
            let successCount = 0;

            for (const row of selectedRows) {
                try {
                    // We could use the batch endpoint but doing one by one allows for better progress updates/UI feedback locally if needed
                    // But let's use the single endpoint to update progress
                    setStatusMsg(`Drafting... ${successCount + 1}/${selectedRows.length}`);
                    await draftSingle(row);
                    successCount++;
                } catch (e) {
                    console.error(e);
                }
            }
            setStatusMsg(`Completed! Drafted ${successCount} emails.`);
        } catch (e) {
            setStatusMsg('Error during batch process.');
        } finally {
            setProcessing(false);
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center text-blue-400"><Loader2 className="animate-spin" size={48} /></div>;

    return (
        <div className="min-h-screen p-8">
            <div className="max-w-7xl mx-auto space-y-6">
                <header className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="p-2 bg-white/5 rounded-full hover:bg-white/10 transition-colors"><ArrowLeft /></Link>
                        <h1 className="text-3xl font-bold">Email Draft Mode</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-sm text-gray-400">
                            {selectedIndices.size} selected
                        </div>
                        <button
                            onClick={handleDraftSelected}
                            disabled={processing || selectedIndices.size === 0}
                            className={`px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 transition-colors font-medium text-white shadow-lg shadow-blue-500/30 flex items-center gap-2 ${processing ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {processing ? <Loader2 className="animate-spin" /> : <Save />}
                            {processing ? 'Processing...' : 'Save as Drafts'}
                        </button>
                    </div>
                </header>

                {statusMsg && (
                    <div className="p-4 rounded bg-blue-500/10 border border-blue-500/20 text-blue-200">
                        {statusMsg}
                    </div>
                )}

                <div className="glass-panel rounded-xl overflow-hidden">
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
