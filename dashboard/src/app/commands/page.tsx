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
                <span className="loading loading-spinner loading-lg text-primary"></span>
            </div>
        );
    }

    const categories = ['all', ...new Set(commands.map(c => c.cog))];
    const filteredCommands = filter === 'all' ? commands : commands.filter(c => c.cog === filter);

    return (
        <div className="min-h-screen bg-base-200">
            <Header>
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
                    <div>
                        <h2 className="text-2xl font-bold text-base-content">Command Management</h2>
                        <p className="text-base-content/60">View and explore all available bot commands</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {categories.map(cat => (
                            <button
                                key={cat}
                                onClick={() => setFilter(cat)}
                                className={`btn btn-sm ${filter === cat ? 'btn-primary' : 'btn-ghost'}`}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Command Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                        [...Array(6)].map((_, i) => (
                            <div key={i} className="card bg-base-100 shadow-md border border-base-300 animate-pulse">
                                <div className="card-body p-6 h-48">
                                    <div className="flex items-center gap-4 mb-4">
                                        <div className="w-12 h-12 bg-base-300 rounded-xl"></div>
                                        <div className="flex-1 space-y-2">
                                            <div className="h-4 bg-base-300 rounded w-3/4"></div>
                                            <div className="h-3 bg-base-300 rounded w-1/2"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : filteredCommands.length > 0 ? (
                        filteredCommands.map(cmd => (
                            <div key={cmd.name} className="card bg-base-100 shadow-md border border-base-300 hover:border-primary/50 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group">
                                <div className="card-body p-5">
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex items-center gap-3">
                                            <div className="w-11 h-11 bg-primary/10 rounded-xl flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                                                <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                </svg>
                                            </div>
                                            <div>
                                                <h4 className="font-bold text-base-content">{cmd.name}</h4>
                                                <span className="badge badge-sm badge-outline">{cmd.cog}</span>
                                            </div>
                                        </div>
                                        {cmd.hidden && <span className="badge badge-error badge-sm">Hidden</span>}
                                    </div>

                                    <p className="text-sm text-base-content/60 line-clamp-2 mb-4 min-h-[40px]">
                                        {cmd.description || "No description available for this command."}
                                    </p>

                                    <div className="flex items-center justify-between mt-auto">
                                        {cmd.aliases && cmd.aliases.length > 0 && (
                                            <div className="flex flex-wrap gap-1">
                                                {cmd.aliases.slice(0, 3).map(alias => (
                                                    <span key={alias} className="text-[10px] bg-base-200 text-base-content/50 px-2 py-0.5 rounded">{alias}</span>
                                                ))}
                                            </div>
                                        )}
                                        {isAuthorizedUser ? (
                                            <label className="label cursor-pointer gap-2">
                                                <input
                                                    type="checkbox"
                                                    className="toggle toggle-primary toggle-sm"
                                                    checked={cmd.enable}
                                                    onChange={() => handleToggle(cmd.name, cmd.enable)}
                                                    disabled={toggling === cmd.name}
                                                />
                                                <span className="label-text text-xs">{cmd.enable ? 'On' : 'Off'}</span>
                                            </label>
                                        ) : (
                                            <span className={`badge badge-sm ${cmd.enable ? 'badge-success' : 'badge-error'}`}>
                                                {cmd.enable ? 'Enabled' : 'Disabled'}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full">
                            <div className="text-center py-20">
                                <div className="text-6xl mb-4">🔍</div>
                                <h3 className="text-xl font-medium text-base-content">No commands found</h3>
                                <p className="text-base-content/50">Try adjusting your filters.</p>
                            </div>
                        </div>
                    )}
                </div>
            </Header>
        </div>
    );
}
