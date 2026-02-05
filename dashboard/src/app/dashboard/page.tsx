'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { statsApi, StatsOverview } from '@/lib/api';
import Link from 'next/link';

export default function DashboardPage() {
    const { user, token, isLoading, logout } = useAuth();
    const router = useRouter();

    const [stats, setStats] = useState<StatsOverview | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/');
        }
    }, [user, isLoading, router]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const overviewData = await statsApi.getOverview();
                setStats(overviewData);
            } catch (error) {
                console.error('Failed to fetch overview data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

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

    const guildIconUrl = stats?.guild?.id && stats?.guild?.icon
        ? `https://cdn.discordapp.com/icons/${stats.guild.id}/${stats.guild.icon}.png`
        : null;

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
                    <h2 className="text-3xl font-bold mb-2">Welcome back, {user.username}!</h2>
                    <p className="text-gray-400 text-lg">Managing the bot for your community</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Guild Info Card */}
                    <div className="lg:col-span-2">
                        <div className="glass rounded-2xl overflow-hidden">
                            <div className="h-32 bg-gradient-to-r from-purple-900/40 to-cyan-900/40 relative">
                                {guildIconUrl && (
                                    <div className="absolute -bottom-10 left-8">
                                        <img
                                            src={guildIconUrl}
                                            alt={stats?.guild?.name}
                                            className="w-24 h-24 rounded-2xl ring-4 ring-gray-900 bg-gray-900 shadow-2xl"
                                        />
                                    </div>
                                )}
                            </div>
                            <div className="p-8 pt-12">
                                <div className="flex flex-col gap-6">
                                    <div>
                                        <h3 className="text-2xl font-bold mb-1">{stats?.guild?.name || 'Unknown Guild'}</h3>
                                        <p className="text-gray-400 text-sm tracking-widest uppercase">Discord Server Information</p>
                                    </div>

                                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
                                        <div className="space-y-1">
                                            <p className="text-xs text-gray-500 uppercase font-semibold">Members</p>
                                            <p className="text-xl font-medium">{stats?.guild?.members || 'N/A'}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-xs text-gray-500 uppercase font-semibold">Guild ID</p>
                                            <p className="text-sm font-mono truncate text-gray-300">{stats?.guild?.id || 'N/A'}</p>
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-xs text-gray-500 uppercase font-semibold">Region</p>
                                            <p className="text-xl font-medium">{stats?.guild?.region || 'Classic'}</p>
                                        </div>
                                    </div>

                                    <div className="flex gap-4">
                                        <Link
                                            href="/commands"
                                            className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-xl transition-all shadow-lg shadow-purple-600/20 active:scale-95"
                                        >
                                            Manage Commands
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Bot Side Card */}
                    <div className="space-y-6">
                        <div className="glass p-6 rounded-2xl border border-white/5">
                            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Bot Health</h4>
                            <div className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl border border-white/5">
                                <div className="flex items-center gap-3">
                                    <div className={`w-3 h-3 rounded-full ${stats?.bot_status === 'online' ? 'bg-green-500 pulse-glow' : 'bg-gray-500'}`} />
                                    <span className="font-medium">System Status</span>
                                </div>
                                <span className={`text-sm font-bold uppercase ${stats?.bot_status === 'online' ? 'text-green-400' : 'text-gray-400'}`}>
                                    {stats?.bot_status || 'Offline'}
                                </span>
                            </div>
                        </div>

                        <div className="glass p-6 rounded-2xl border border-white/5">
                            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Quick Links</h4>
                            <div className="space-y-3">
                                <a href="https://discord.com" target="_blank" className="flex items-center justify-between p-3 hover:bg-gray-800/40 rounded-lg transition-colors group">
                                    <span className="text-gray-300 group-hover:text-white">Discord Support</span>
                                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" /></svg>
                                </a>
                                <a href="#" className="flex items-center justify-between p-3 hover:bg-gray-800/40 rounded-lg transition-colors group">
                                    <span className="text-gray-300 group-hover:text-white">Documentation</span>
                                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" /></svg>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
