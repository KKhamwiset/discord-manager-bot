'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { commandsApi, Command } from '@/lib/api';
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

    useEffect(() => { getAuthData(); }, [user, logout]);

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
            <div className="min-h-screen flex items-center justify-center bg-base-200">
                <span className="loading loading-spinner loading-md text-primary"></span>
            </div>
        );
    }

    const categories = ['all', ...new Set(commands.map(c => c.cog))];
    const filteredCommands = filter === 'all' ? commands : commands.filter(c => c.cog === filter);

    return (
        <div className="min-h-screen bg-base-200">
            <Header>
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                        <div>
                            <h1 className="text-2xl font-semibold text-base-content">Commands</h1>
                            <p className="text-sm text-base-content/50 mt-1">{commands.length} total commands</p>
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {categories.map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => setFilter(cat)}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors capitalize ${
                                        filter === cat
                                            ? 'bg-primary text-primary-content'
                                            : 'text-base-content/60 hover:text-base-content hover:bg-base-200'
                                    }`}
                                >
                                    {cat}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Table — Linear style */}
                    <div className="bg-base-100 rounded-lg border border-base-300 overflow-hidden">
                        {/* Table Header */}
                        <div className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-base-300 text-xs font-medium text-base-content/50 uppercase tracking-wider">
                            <div className="col-span-4">Name</div>
                            <div className="col-span-2">Category</div>
                            <div className="col-span-4">Description</div>
                            <div className="col-span-2 text-right">Status</div>
                        </div>

                        {/* Table Body */}
                        {loading ? (
                            [...Array(6)].map((_, i) => (
                                <div key={i} className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-base-300/50 animate-pulse">
                                    <div className="col-span-4"><div className="h-4 bg-base-200 rounded w-3/4"></div></div>
                                    <div className="col-span-2"><div className="h-4 bg-base-200 rounded w-1/2"></div></div>
                                    <div className="col-span-4"><div className="h-4 bg-base-200 rounded w-full"></div></div>
                                    <div className="col-span-2"><div className="h-4 bg-base-200 rounded w-1/2 ml-auto"></div></div>
                                </div>
                            ))
                        ) : filteredCommands.length > 0 ? (
                            filteredCommands.map(cmd => (
                                <div key={cmd.name} className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-base-300/50 hover:bg-base-200/30 transition-colors group">
                                    <div className="col-span-4 flex items-center gap-3">
                                        <div className="w-8 h-8 bg-primary/10 rounded-md flex items-center justify-center flex-shrink-0">
                                            <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-base-content">{cmd.name}</p>
                                            {cmd.aliases && cmd.aliases.length > 0 && (
                                                <p className="text-xs text-base-content/30">{cmd.aliases.join(', ')}</p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="col-span-2 flex items-center">
                                        <span className="badge badge-sm badge-outline">{cmd.cog}</span>
                                    </div>
                                    <div className="col-span-4 flex items-center">
                                        <p className="text-sm text-base-content/50 truncate">{cmd.description || 'No description'}</p>
                                    </div>
                                    <div className="col-span-2 flex items-center justify-end">
                                        {cmd.hidden && <span className="badge badge-error badge-sm mr-2">Hidden</span>}
                                        {isAuthorizedUser ? (
                                            <label className="label cursor-pointer gap-2">
                                                <input
                                                    type="checkbox"
                                                    className="toggle toggle-primary toggle-sm"
                                                    checked={cmd.enable}
                                                    onChange={() => handleToggle(cmd.name, cmd.enable)}
                                                    disabled={toggling === cmd.name}
                                                />
                                                <span className="label-text text-xs text-base-content/50">{cmd.enable ? 'On' : 'Off'}</span>
                                            </label>
                                        ) : (
                                            <span className={`text-xs font-medium ${cmd.enable ? 'text-success' : 'text-base-content/30'}`}>
                                                {cmd.enable ? 'Enabled' : 'Disabled'}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="py-16 text-center">
                                <p className="text-base-content/40">No commands found</p>
                            </div>
                        )}
                    </div>
                </div>
            </Header>
        </div>
    );
}
