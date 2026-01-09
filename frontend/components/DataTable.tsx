'use client';

import { useState } from 'react';
import { RowData, previewEmail } from '@/lib/api';
import { Eye, CheckSquare, Square } from 'lucide-react';

interface DataTableProps {
    rows: RowData[];
    selectedIndices: Set<number>;
    onToggleSelect: (index: number) => void;
    onToggleAll: (selectAll: boolean) => void;
}

export default function DataTable({ rows, selectedIndices, onToggleSelect, onToggleAll }: DataTableProps) {
    const [previewData, setPreviewData] = useState<{ subject: string, body: string } | null>(null);
    const [isPreviewOpen, setIsPreviewOpen] = useState(false);

    const handlePreview = async (data: any) => {
        try {
            const res = await previewEmail(data);
            setPreviewData(res);
            setIsPreviewOpen(true);
        } catch (e) {
            alert('Failed to preview');
        }
    };

    const allSelected = rows.length > 0 && selectedIndices.size === rows.length;

    return (
        <>
            <div className="w-full overflow-x-auto rounded-lg border border-white/10">
                <table className="w-full text-left text-sm text-gray-400">
                    <thead className="bg-white/5 text-xs uppercase text-gray-200">
                        <tr>
                            <th className="p-4 w-4">
                                <button onClick={() => onToggleAll(!allSelected)} className="hover:text-white">
                                    {allSelected ? <CheckSquare size={18} /> : <Square size={18} />}
                                </button>
                            </th>
                            <th className="p-4">Name</th>
                            <th className="p-4">Email</th>
                            <th className="p-4">Channel</th>
                            <th className="p-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                        {rows.map((row) => {
                            const isSelected = selectedIndices.has(row.row_index);
                            return (
                                <tr key={row.row_index} className={`hover:bg-white/5 transition-colors ${isSelected ? 'bg-blue-500/10' : ''}`}>
                                    <td className="p-4">
                                        <button onClick={() => onToggleSelect(row.row_index)} className={isSelected ? 'text-blue-400' : 'text-gray-600'}>
                                            {isSelected ? <CheckSquare size={18} /> : <Square size={18} />}
                                        </button>
                                    </td>
                                    <td className="p-4 text-white font-medium">{row.data.name || 'N/A'}</td>
                                    <td className="p-4">{row.data.email || 'N/A'}</td>
                                    <td className="p-4">{row.data.channel || 'N/A'}</td>
                                    <td className="p-4 text-right">
                                        <button
                                            onClick={() => handlePreview(row.data)}
                                            className="p-2 hover:bg-white/10 rounded-full text-blue-400 transition-colors"
                                            title="Preview Email"
                                        >
                                            <Eye size={18} />
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {isPreviewOpen && previewData && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-[#1a1a1a] border border-white/10 rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
                        <div className="p-6 border-b border-white/10 flex justify-between items-center">
                            <h3 className="text-xl font-bold text-white">Email Preview</h3>
                            <button onClick={() => setIsPreviewOpen(false)} className="text-gray-400 hover:text-white">Close</button>
                        </div>
                        <div className="p-6 overflow-y-auto space-y-4">
                            <div>
                                <label className="text-xs uppercase text-gray-500 font-bold">Subject</label>
                                <div className="text-white text-lg">{previewData.subject}</div>
                            </div>
                            <div>
                                <label className="text-xs uppercase text-gray-500 font-bold">Body</label>
                                <div className="text-gray-300 whitespace-pre-wrap mt-2 p-4 bg-white/5 rounded-lg border border-white/5 font-mono text-sm">
                                    {previewData.body}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
