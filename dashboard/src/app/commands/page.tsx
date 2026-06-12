'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { commandsApi, Command } from '@/lib/api';
import Link from 'next/link';
import Header from '@/components/Header';
import { authApi } from '@/lib/api';

export default function CommandsPage() {
    const { user, token, isLoading, logout } = useAuth();
    const router = useRouter();
    const [commands, setCommands] = useState<Command[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');
    const [toggling, setToggling] = useState<string | null>(null);
    const [isAuthorizedUser, setIsAuthorizedUser] = useState(false);
    async function getAuthData() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            try {
                const authData = await authApi.authorizedUser(token);
                setIsAuthorizedUser(authData.authorized);
            } catch (error) {
                console.error('Failed to get authorized user data:', error);
            }
        }
        return null;
    }
    useEffect(() => {
        getAuthData();
    },[user, logout]);

    const handleToggle = async (commandName: string, currentStatus: boolean) => {
        if (!token || toggling) return;
        setToggling(commandName);
        try {
            await commandsApi.toggle(token, commandName, !currentStatus);
            setCommands(prev => prev.map(cmd =>
                cmd.name === commandName ? { ...cmd, enable: !currentStatus } : cmd
            ));
        } catch (error) {
            console.error('Failed to toggle command:', error);
        } finally {
            setToggling(null);
        }
    };

    useEffect(() => {
        if (!isLoading && !user) { router.push('/'); }
    }, [user, isLoading, router]);

    useEffect(() => {
        const fetchData = async () => {
            if (!token) return;
            try {
                const [cmdData] = await Promise.all([commandsApi.list(token)]);
                setCommands(cmdData.commands || []);
            } catch (error) {
                console.error('Failed to fetch commands:', error);
            } finally {
                setLoading(false);
            }
        };
        if (token) { fetchData(); }
    }, [token]);

    if (isLoading || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-pink-500"></div>
            </div>
        );
    }

    const categories = ['all', ...new Set(commands.map(c => c.cog))];
    const filteredCommands = filter === 'all' ? commands : commands.filter(c => c.cog === filter);

    return (
        <div className="min-h-screen">
            <Header />
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
                    <div>
                        <h2 className="text-2xl font-bold mb-2 text-[#2d1028]">Command Management</h2>
                        <p className="text-[#6b3a5a]">View and explore all available bot commands</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {categories.map(cat => (
                            <button key={cat} onClick={() => setFilter(cat)}
                                className={`px-4 py-2 text-sm font-medium rounded-xl transition-all duration-200 capitalize ${filter === cat ? 'bg-[#d6197e] text-white shadow-lg shadow-pink-500/25' : 'bg-[#fff5f8] text-[#6b3a5a] hover:text-[#2d1028] border border-[#e8b4c8] hover:border-[#d6197e]'}`}
                            >{cat}</button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                        [...Array(6)].map((_, i) => (
                            <div key={i} className="glass rounded-xl p-6 h-48 animate-pulse border border-[#e8b4c8]">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="w-12 h-12 bg-[#ffe0ec] rounded-lg" />
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 bg-[#ffe0ec] rounded w-3/4" />
                                        <div className="h-3 bg-[#ffe0ec] rounded w-1/2" />
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : filteredCommands.length > 0 ? (
                        filteredCommands.map(cmd => (
                            <div key={cmd.name} className="glass rounded-xl p-6 border border-[#e8b4c8] group hover:border-[#d6197e] transition-all duration-300 hover:translate-y-[-4px]">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-pink-100 rounded-xl flex items-center justify-center group-hover:bg-pink-200 transition-colors">
                                            <svg className="w-6 h-6 text-[#d6197e]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-lg text-[#2d1028]">{cmd.name}</h4>
                                            <span className="text-xs font-medium px-2 py-0.5 bg-[#fff5f8] text-[#8b5a7a] rounded-full uppercase tracking-wider border border-[#e8b4c8]">{cmd.cog}</span>
                                        </div>
                                    </div>
                                    {cmd.hidden && <span className="text-[10px] bg-red-50 text-red-600 px-2 py-1 rounded-md font-bold uppercase tracking-tight border border-red-200">Hidden</span>}
                                    {isAuthorizedUser ? (
                                        <button onClick={() => handleToggle(cmd.name, cmd.enable)} disabled={toggling === cmd.name}
                                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-offset-2 focus:ring-offset-white ${cmd.enable ? 'bg-[#d6197e]' : 'bg-[#e8b4c8]'} ${toggling === cmd.name ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
                                            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${cmd.enable ? 'translate-x-6' : 'translate-x-1'}`} />
                                        </button>
                                    ) : (
                                        cmd.enable ? (
                                            <span className="text-[10px] bg-green-50 text-green-700 px-2 py-1 rounded-md font-bold uppercase tracking-tight border border-green-200">Enabled</span>
                                        ) : (
                                            <span className="text-[10px] bg-red-50 text-red-600 px-2 py-1 rounded-md font-bold uppercase tracking-tight border border-red-200">Disabled</span>
                                        )
                                    )}
                                </div>
                                <p className="text-sm text-[#6b3a5a] line-clamp-2 mb-4 min-h-[40px]">{cmd.description || "No description available for this command."}</p>
                                {cmd.aliases && cmd.aliases.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mt-auto">
                                        {cmd.aliases.map(alias => (
                                            <span key={alias} className="text-[10px] bg-[#fff5f8] text-[#8b5a7a] px-2 py-1 rounded border border-[#e8b4c8]">{alias}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full py-20 text-center">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-pink-100 text-[#d6197e] mb-4">
                                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                            </div>
                            <h3 className="text-xl font-medium text-[#2d1028]">No commands found</h3>
                            <p className="text-[#6b3a5a]">Try adjusting your filters or search query.</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
