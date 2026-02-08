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
            <div className="bg-[#0f0f13] border border-gray-800 rounded-xl shadow-2xl p-4 flex items-center gap-4 min-w-[320px] backdrop-blur-md bg-opacity-90">
                <div className="flex-1">
                    <p className="text-white font-medium text-sm">Unsaved Changes</p>
                    <p className="text-gray-400 text-xs">You have modifications that haven't been saved.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={onDiscard}
                        disabled={loading}
                        className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-colors disabled:opacity-50"
                    >
                        Discard
                    </button>
                    <button
                        onClick={onSave}
                        disabled={loading}
                        className="px-3 py-1.5 rounded-lg text-sm font-medium bg-purple-600 hover:bg-purple-500 text-white transition-colors shadow-lg shadow-purple-500/20 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading && (
                            <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        )}
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
}
