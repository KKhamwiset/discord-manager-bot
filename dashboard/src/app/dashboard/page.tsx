'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { statsApi, StatsOverview, CommandStat, ActivityData } from '@/lib/api';
import Link from 'next/link';

export default function DashboardPage() {
    const { user, token, isLoading, logout } = useAuth();
    const router = useRouter();
    const [stats, setStats] = useState<StatsOverview | null>(null);
    const [commandStats, setCommandStats] = useState<CommandStat[]>([]);
    const [activity, setActivity] = useState<ActivityData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/');
        }
    }, [user, isLoading, router]);

    useEffect(() => {
        const fetchData = async () => {
            if (!token) return;

            try {
                const [overviewData, cmdData, activityData] = await Promise.all([
                    statsApi.getOverview(token),
                    statsApi.getCommandStats(token),
                    statsApi.getActivity(token),
                ]);

                setStats(overviewData);
                setCommandStats(cmdData.commands || []);
                setActivity(activityData.activity || []);
            } catch (error) {
                console.error('Failed to fetch stats:', error);
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

    const avatarUrl = user.avatar
        ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
        : `https://cdn.discordapp.com/embed/avatars/${parseInt(user.id) % 5}.png`;

    return (
        <div className="min-h-screen">
            {/* Header */}
            <header className="glass sticky top-0 z-50 border-b border-gray-800">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center gap-8">
                            <h1 className="text-xl font-bold gradient-text">Bot Dashboard</h1>
                            <nav className="hidden md:flex gap-6">
                                <Link href="/dashboard" className="text-white font-medium">
                                    Overview
                                </Link>
                                <Link href="/commands" className="text-gray-400 hover:text-white transition-colors">
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
                {/* Welcome Section */}
                <div className="mb-8">
                    <h2 className="text-2xl font-bold mb-2">Welcome back, {user.username}!</h2>
                    <p className="text-gray-400">Here&apos;s what&apos;s happening with your bot</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="glass p-6 rounded-xl card-hover">
                        <div className="flex items-center justify-between mb-4">
                            <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                                <div className="w-3 h-3 bg-green-500 rounded-full pulse-glow"></div>
                            </div>
                            <span className="text-xs text-green-400 font-medium">ONLINE</span>
                        </div>
                        <h3 className="text-2xl font-bold">{stats?.bot_status || 'Online'}</h3>
                        <p className="text-sm text-gray-400">Bot Status</p>
                    </div>

                    <div className="glass p-6 rounded-xl card-hover">
                        <div className="flex items-center justify-between mb-4">
                            <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                        </div>
                        <h3 className="text-2xl font-bold">{stats?.total_commands?.toLocaleString() || '0'}</h3>
                        <p className="text-sm text-gray-400">Total Commands</p>
                    </div>

                    <div className="glass p-6 rounded-xl card-hover">
                        <div className="flex items-center justify-between mb-4">
                            <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                        <h3 className="text-2xl font-bold">{stats?.commands_24h?.toLocaleString() || '0'}</h3>
                        <p className="text-sm text-gray-400">Commands (24h)</p>
                    </div>

                    <div className="glass p-6 rounded-xl card-hover">
                        <div className="flex items-center justify-between mb-4">
                            <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                                </svg>
                            </div>
                        </div>
                        <h3 className="text-2xl font-bold">{commandStats.length || '0'}</h3>
                        <p className="text-sm text-gray-400">Active Commands</p>
                    </div>
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Activity Chart */}
                    <div className="glass p-6 rounded-xl">
                        <h3 className="text-lg font-semibold mb-4">Activity (Last 7 Days)</h3>
                        {loading ? (
                            <div className="h-48 flex items-center justify-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
                            </div>
                        ) : activity.length > 0 ? (
                            <div className="h-48 flex items-end gap-2">
                                {activity.map((day, i) => {
                                    const maxCommands = Math.max(...activity.map(d => d.commands), 1);
                                    const height = (day.commands / maxCommands) * 100;
                                    return (
                                        <div key={i} className="flex-1 flex flex-col items-center gap-2">
                                            <div
                                                className="w-full bg-gradient-to-t from-purple-600 to-cyan-500 rounded-t-lg transition-all duration-300 hover:opacity-80"
                                                style={{ height: `${Math.max(height, 5)}%` }}
                                                title={`${day.commands} commands`}
                                            />
                                            <span className="text-xs text-gray-500">{day.date.slice(-5)}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="h-48 flex items-center justify-center text-gray-500">
                                No activity data yet
                            </div>
                        )}
                    </div>

                    {/* Top Commands */}
                    <div className="glass p-6 rounded-xl">
                        <h3 className="text-lg font-semibold mb-4">Top Commands</h3>
                        {loading ? (
                            <div className="space-y-3">
                                {[...Array(5)].map((_, i) => (
                                    <div key={i} className="h-10 bg-gray-800 rounded animate-pulse" />
                                ))}
                            </div>
                        ) : commandStats.length > 0 ? (
                            <div className="space-y-3">
                                {commandStats.slice(0, 5).map((cmd, i) => (
                                    <div key={cmd.command} className="flex items-center gap-3">
                                        <span className="w-6 text-sm text-gray-500">{i + 1}</span>
                                        <div className="flex-1">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="font-medium">{cmd.command}</span>
                                                <span className="text-sm text-gray-400">{cmd.usage_count}</span>
                                            </div>
                                            <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-purple-600 to-cyan-500 rounded-full"
                                                    style={{ width: `${(cmd.usage_count / commandStats[0].usage_count) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="h-48 flex items-center justify-center text-gray-500">
                                No command data yet
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
