import React from 'react';

interface UnsavedChangesToastProps {
    isOpen: boolean;
    count?: number;
    onSave: () => void;
    onDiscard: () => void;
    loading?: boolean;
}

export default function UnsavedChangesToast({ isOpen, count, onSave, onDiscard, loading = false }: UnsavedChangesToastProps) {
    if (!isOpen) return null;

    const summary = count === undefined
        ? 'Nothing is saved until you press Save.'
        : `${count} ${count === 1 ? 'change' : 'changes'} not saved yet.`;

    return (
        <div className="fixed inset-x-4 bottom-4 z-50 mx-auto max-w-lg sm:bottom-6" role="status">
            <div className="flex flex-col gap-3 border-4 border-pink-950 bg-white p-3 shadow-[8px_8px_0_#8a174d] sm:flex-row sm:items-center">
                <div className="flex-1">
                    <p className="text-sm font-black uppercase text-pink-950">Unsaved changes</p>
                    <p className="text-sm font-medium text-pink-900">{summary}</p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={onDiscard} disabled={loading} className="pixel-button-light flex-1 px-3 py-2 text-xs sm:flex-none">
                        Discard
                    </button>
                    <button onClick={onSave} disabled={loading} className="pixel-button inline-flex flex-1 items-center justify-center gap-2 px-4 py-2 text-xs sm:flex-none">
                        {loading && <span className="loading loading-spinner loading-xs" aria-hidden="true"></span>}
                        {loading ? 'Saving' : 'Save'}
                    </button>
                </div>
            </div>
        </div>
    );
}
