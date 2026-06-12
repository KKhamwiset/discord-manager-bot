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
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 animate-fade-in-up">
            <div className="bg-base-100 border border-base-300 rounded-xl shadow-2xl p-4 flex items-center gap-4 min-w-[320px]">
                <div className="flex-1">
                    <p className="text-base-content font-medium text-sm">Unsaved Changes</p>
                    <p className="text-base-content/50 text-xs">You have modifications that haven&apos;t been saved.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={onDiscard} disabled={loading} className="btn btn-sm btn-ghost">Discard</button>
                    <button onClick={onSave} disabled={loading} className="btn btn-sm btn-primary">
                        {loading && <span className="loading loading-spinner loading-xs"></span>}
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
}
