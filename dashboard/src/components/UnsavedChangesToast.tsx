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
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
            <div className="bg-base-100 border border-base-300 rounded-lg shadow-2xl p-3 flex items-center gap-3 min-w-[300px]">
                <div className="flex-1">
                    <p className="text-base-content font-medium text-sm">Unsaved changes</p>
                    <p className="text-base-content/40 text-xs">You have unsaved modifications.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={onDiscard} disabled={loading} className="btn btn-xs btn-ghost">Discard</button>
                    <button onClick={onSave} disabled={loading} className="btn btn-xs btn-primary">
                        {loading && <span className="loading loading-spinner loading-xs"></span>}
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
}
