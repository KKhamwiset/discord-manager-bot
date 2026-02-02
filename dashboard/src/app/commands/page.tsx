'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { commandsApi, Command, CommandLog } from '@/lib/api';
import Link from 'next/link';

export default function CommandsPage() {
    const { user, token, isLoading, logout } = useAuth();
    const router = useRouter();
    const [commands, setCommands] = useState<Command[]>([]);
    const [logs, setLogs] = useState<CommandLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');
    const [updating, setUpdating] = useState<string | null>(null);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/');
        }
    }, [user, isLoading, router]);

    useEffect(() => {
        const fetchData = async () => {
            if (!token) return;

            try {
                const [cmdData, logsData] = await Promise.all([
                    commandsApi.list(token),
                    commandsApi.getLogs(token, 20),
                ]);

                setCommands(cmdData.commands || []);
                setLogs(logsData.logs || []);
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

    const toggleCommand = async (commandName: string, currentEnabled: boolean) => {
        if (!token) return;

        setUpdating(commandName);
        try {
            await commandsApi.toggle(token, commandName, !currentEnabled);
            setCommands(prev =>
                prev.map(cmd =>
                    cmd.name === commandName ? { ...cmd, enabled: !currentEnabled } : cmd
                )
            );
        } catch (error) {
            console.error('Failed to toggle command:', error);
        } finally {
            setUpdating(null);
        }
    };

    if (isLoading || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    const avatarUrl = user.avatar
        ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
        : `https://cdn.discordapp.com/embed/avatars/${parseInt(user.id) % 5}.png`;

    const categories = ['all', ...new Set(commands.map(c => c.category))];
    const filteredCommands = filter === 'all'
        ? commands
        : commands.filter(c => c.category === filter);

    const formatTime = (timestamp: number) => {
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    };

    return (
        <div className="min-h-screen">
            {/* Header */}
            <header className="glass sticky top-0 z-50 border-b border-gray-800">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center gap-8">
                            <h1 className="text-xl font-bold gradient-text">Bot Dashboard</h1>
                            <nav className="hidden md:flex gap-6">
                                <Link href="/dashboard" className="text-gray-400 hover:text-white transition-colors">
                                    Overview
                                </Link>
                                <Link href="/commands" className="text-white font-medium">
                                    Commands
                                </Link>
                            </nav>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-3">
                                <img
                                    src={avatarUrl}
                                    alt={user.username}
                                    className="w-8 h-8 rounded-full ring-2 ring-purple-500/50"
                                />
                                <span className="text-sm font-medium hidden sm:block">{user.username}</span>
                            </div>
                            <button
                                onClick={logout}
                                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold mb-2">Command Management</h2>
                    <p className="text-gray-400">Enable or disable bot commands</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Commands List */}
                    <div className="lg:col-span-2">
                        <div className="glass rounded-xl overflow-hidden">
                            {/* Filter Tabs */}
                            <div className="p-4 border-b border-gray-800 flex flex-wrap gap-2">
                                {categories.map(cat => (
                                    <button
                                        key={cat}
                                        onClick={() => setFilter(cat)}
                                        className={`px-3 py-1.5 text-sm rounded-lg transition-colors capitalize ${filter === cat
                                                ? 'bg-purple-600 text-white'
                                                : 'bg-gray-800 text-gray-400 hover:text-white'
                                            }`}
                                    >
                                        {cat}
                                    </button>
                                ))}
                            </div>

                            {/* Command Table */}
                            <div className="divide-y divide-gray-800">
                                {loading ? (
                                    [...Array(5)].map((_, i) => (
                                        <div key={i} className="p-4 flex items-center gap-4">
                                            <div className="h-10 w-24 bg-gray-800 rounded animate-pulse" />
                                            <div className="flex-1 h-4 bg-gray-800 rounded animate-pulse" />
                                            <div className="h-6 w-12 bg-gray-800 rounded animate-pulse" />
                                        </div>
                                    ))
                                ) : filteredCommands.length > 0 ? (
                                    filteredCommands.map(cmd => (
                                        <div key={cmd.name} className="p-4 flex items-center justify-between hover:bg-gray-800/50 transition-colors">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                                                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <h4 className="font-medium">{cmd.name}</h4>
                                                    <p className="text-sm text-gray-500">{cmd.category}</p>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-4">
                                                <span className="text-sm text-gray-500">{cmd.usage_count} uses</span>
                                                <button
                                                    onClick={() => toggleCommand(cmd.name, cmd.enabled)}
                                                    disabled={updating === cmd.name}
                                                    className={`relative w-12 h-6 rounded-full transition-colors ${cmd.enabled ? 'bg-green-600' : 'bg-gray-700'
                                                        }`}
                                                >
                                                    <span
                                                        className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${cmd.enabled ? 'left-7' : 'left-1'
                                                            } ${updating === cmd.name ? 'opacity-50' : ''}`}
                                                    />
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="p-8 text-center text-gray-500">
                                        No commands found
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Recent Logs */}
                    <div className="glass rounded-xl p-4">
                        <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
                        {loading ? (
                            <div className="space-y-3">
                                {[...Array(5)].map((_, i) => (
                                    <div key={i} className="h-16 bg-gray-800 rounded animate-pulse" />
                                ))}
                            </div>
                        ) : logs.length > 0 ? (
                            <div className="space-y-3 max-h-[600px] overflow-y-auto">
                                {logs.map((log, i) => (
                                    <div key={i} className="p-3 bg-gray-800/50 rounded-lg">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="font-medium text-sm">{log.command}</span>
                                            <span className={`w-2 h-2 rounded-full ${log.success ? 'bg-green-500' : 'bg-red-500'}`} />
                                        </div>
                                        <p className="text-xs text-gray-500">by {log.user}</p>
                                        <p className="text-xs text-gray-600">{formatTime(log.timestamp)}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-8">
                                No recent activity
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
