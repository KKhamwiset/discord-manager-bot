'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { commandsApi, Command } from '@/lib/api';
import Link from 'next/link';
import Header from '@/components/Header';

export default function CommandsPage() {
    const { user, token, isLoading, logout } = useAuth();
    const router = useRouter();
    const [commands, setCommands] = useState<Command[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/');
        }
    }, [user, isLoading, router]);

    useEffect(() => {
        const fetchData = async () => {
            if (!token) return;

            try {
                const [cmdData] = await Promise.all([
                    commandsApi.list(token),
                ]);

                setCommands(cmdData.commands || []);
            } catch (error) {
                console.error('Failed to fetch commands:', error);
            } finally {
                setLoading(false);
            }
        };

        if (token) {
            fetchData();
        }
    }, [token]);


    if (isLoading || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }


    const categories = ['all', ...new Set(commands.map(c => c.cog))];
    const filteredCommands = filter === 'all'
        ? commands
        : commands.filter(c => c.cog === filter);


    return (
        <div className="min-h-screen">
            <Header />

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
                    <div>
                        <h2 className="text-2xl font-bold mb-2">Command Management</h2>
                        <p className="text-gray-400">View and explore all available bot commands</p>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {categories.map(cat => (
                            <button
                                key={cat}
                                onClick={() => setFilter(cat)}
                                className={`px-4 py-2 text-sm font-medium rounded-xl transition-all duration-200 capitalize ${filter === cat
                                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/25'
                                    : 'bg-gray-800/50 text-gray-400 hover:text-white border border-gray-800 hover:border-gray-700'
                                    }`}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                        [...Array(6)].map((_, i) => (
                            <div key={i} className="glass rounded-xl p-6 h-48 animate-pulse">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="w-12 h-12 bg-gray-800 rounded-lg" />
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 bg-gray-800 rounded w-3/4" />
                                        <div className="h-3 bg-gray-800 rounded w-1/2" />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="h-3 bg-gray-800 rounded w-full" />
                                    <div className="h-3 bg-gray-800 rounded w-full" />
                                </div>
                            </div>
                        ))
                    ) : filteredCommands.length > 0 ? (
                        filteredCommands.map(cmd => (
                            <div key={cmd.name} className="glass rounded-xl p-6 group hover:border-purple-500/50 transition-all duration-300 hover:translate-y-[-4px]">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
                                            <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-lg">{cmd.name}</h4>
                                            <span className="text-xs font-medium px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full uppercase tracking-wider">
                                                {cmd.cog}
                                            </span>
                                        </div>
                                    </div>
                                    {cmd.hidden && (
                                        <span className="text-[10px] bg-red-500/10 text-red-400 px-2 py-1 rounded-md font-bold uppercase tracking-tight">
                                            Hidden
                                        </span>
                                    )}
                                </div>

                                <p className="text-sm text-gray-400 line-clamp-2 mb-4 min-h-[40px]">
                                    {cmd.description || "No description available for this command."}
                                </p>

                                {cmd.aliases && cmd.aliases.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mt-auto">
                                        {cmd.aliases.map(alias => (
                                            <span key={alias} className="text-[10px] bg-gray-800/50 text-gray-500 px-2 py-1 rounded">
                                                {alias}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full py-20 text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-800 text-gray-600 mb-4">
                                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-medium text-gray-400">No commands found</h3>
                            <p className="text-gray-500">Try adjusting your filters or search query.</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
