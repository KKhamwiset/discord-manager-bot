'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { statsApi, StatsOverview } from '@/lib/api';
import Link from 'next/link';
import Header from '@/components/Header';
import { authApi } from '@/lib/api';

export default function DashboardPage() {
    const { user, token, isLoading, logout } = useAuth();
    const router = useRouter();
    const [stats, setStats] = useState<StatsOverview | null>(null);
    const [loading, setLoading] = useState(true);
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

    useEffect(() => {
        if (!isLoading && !user) { router.push('/'); }
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
            <div className="min-h-screen flex items-center justify-center bg-base-200">
                <span className="loading loading-spinner loading-lg text-primary"></span>
            </div>
        );
    }

    const guildIconUrl = stats?.guild?.id && stats?.guild?.icon
        ? `https://cdn.discordapp.com/icons/${stats.guild.id}/${stats.guild.icon}.png`
        : null;

    return (
        <div className="min-h-screen bg-base-200">
            <Header>
                {/* Welcome */}
                <div className="mb-8">
                    <h2 className="text-3xl font-bold text-base-content">Welcome back, {user.username}! 🌸</h2>
                    <p className="text-base-content/60 text-lg mt-1">Managing the bot for your community</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    {/* Bot Status Card */}
                    <div className="card bg-base-100 shadow-md border border-base-300">
                        <div className="card-body p-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="card-title text-sm font-semibold text-base-content/60 uppercase tracking-wider">Bot Status</h3>
                                <span className={`w-3 h-3 rounded-full ${stats?.bot_status === 'online' ? 'bg-success animate-pulse' : 'bg-base-content/20'}`}></span>
                            </div>
                            <p className={`text-2xl font-bold ${stats?.bot_status === 'online' ? 'text-success' : 'text-base-content/40'}`}>
                                {stats?.bot_status === 'online' ? 'Online' : 'Offline'}
                            </p>
                            <p className="text-xs text-base-content/50 mt-1">System is {stats?.bot_status || 'checking...'}</p>
                        </div>
                    </div>

                    {/* Members Card */}
                    <div className="card bg-base-100 shadow-md border border-base-300">
                        <div className="card-body p-5">
                            <h3 className="text-sm font-semibold text-base-content/60 uppercase tracking-wider mb-3">Members</h3>
                            <p className="text-2xl font-bold text-primary">{stats?.guild?.members || 'N/A'}</p>
                            <p className="text-xs text-base-content/50 mt-1">Total server members</p>
                        </div>
                    </div>

                    {/* Server Card */}
                    <div className="card bg-base-100 shadow-md border border-base-300">
                        <div className="card-body p-5">
                            <h3 className="text-sm font-semibold text-base-content/60 uppercase tracking-wider mb-3">Server</h3>
                            <p className="text-2xl font-bold text-base-content">{stats?.guild?.name || 'Unknown'}</p>
                            {stats?.guild?.region && <p className="text-xs text-base-content/50 mt-1">Region: {stats.guild.region}</p>}
                        </div>
                    </div>
                </div>

                {/* Server Info Card */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                        <div className="card bg-base-100 shadow-md border border-base-300 overflow-hidden">
                            {/* Banner */}
                            <div className="h-32 bg-gradient-to-r from-pink-300 via-secondary to-purple-300 relative">
                                {guildIconUrl && (
                                    <div className="absolute -bottom-10 left-8">
                                        <div className="avatar">
                                            <div className="w-24 h-24 rounded-2xl ring-4 ring-base-100 bg-base-100 shadow-xl">
                                                <img src={guildIconUrl} alt={stats?.guild?.name} className="rounded-2xl" />
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="card-body pt-14">
                                <h3 className="card-title text-xl">{stats?.guild?.name || 'Unknown Guild'}</h3>
                                <p className="text-base-content/50 text-sm tracking-widest uppercase">Discord Server Information</p>
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-4">
                                    <div>
                                        <p className="text-xs text-base-content/40 uppercase font-semibold">Members</p>
                                        <p className="text-lg font-medium">{stats?.guild?.members || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-base-content/40 uppercase font-semibold">Guild ID</p>
                                        <p className="text-sm font-mono truncate text-base-content/60">{stats?.guild?.id || 'N/A'}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-base-content/40 uppercase font-semibold">Region</p>
                                        <p className="text-lg font-medium">{stats?.guild?.region || 'Classic'}</p>
                                    </div>
                                </div>
                                {isAuthorizedUser && (
                                    <div className="card-actions mt-4">
                                        <Link href="/commands" className="btn btn-primary">
                                            Manage Commands
                                        </Link>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div className="space-y-6">
                        <div className="card bg-base-100 shadow-md border border-base-300">
                            <div className="card-body p-5">
                                <h3 className="card-title text-sm font-semibold text-base-content/60 uppercase tracking-wider mb-3">Quick Links</h3>
                                <div className="space-y-2">
                                    <a href="https://discord.com" target="_blank" className="btn btn-ghost btn-block justify-start gap-3">
                                        <span>💬</span> Discord Support
                                    </a>
                                    <a href="#" className="btn btn-ghost btn-block justify-start gap-3">
                                        <span>📖</span> Documentation
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </Header>
        </div>
    );
}
