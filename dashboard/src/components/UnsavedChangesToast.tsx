import React from 'react';

interface UnsavedChangesToastProps {
    isOpen: boolean;
    onSave: () => void;
    onDiscard: () => void;
    loading?: boolean;
}

export default function UnsavedChangesToast({ isOpen, onSave, onDiscard, loading = false }: UnsavedChangesToastProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 transform">
            <div className="flex min-w-[320px] items-center gap-3 border-4 border-pink-950 bg-white p-3 shadow-[8px_8px_0_#8a174d]">
                <div className="flex-1">
                    <p className="text-sm font-black uppercase text-pink-950">Unsaved changes</p>
                    <p className="text-xs font-bold text-pink-700">You have unsaved modifications.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={onDiscard} disabled={loading} className="border-2 border-pink-950 bg-white px-3 py-1 text-xs font-black uppercase text-pink-950 hover:bg-pink-100 disabled:opacity-60">
                        Discard
                    </button>
                    <button onClick={onSave} disabled={loading} className="border-2 border-pink-950 bg-pink-600 px-3 py-1 text-xs font-black uppercase text-white hover:bg-pink-700 disabled:opacity-60">
                        {loading && <span className="loading loading-spinner loading-xs"></span>}
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
}
