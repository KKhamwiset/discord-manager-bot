'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { statsApi, StatsOverview } from '@/lib/api';
import Link from 'next/link';
import Header from '@/components/Header';
import { authApi } from '@/lib/api';
import { RobotIcon, UsersIcon, ServerIcon, ExternalLinkIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

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
                <span className="loading loading-spinner loading-md text-primary"></span>
            </div>
        );
    }

    const guildIconUrl = stats?.guild?.id && stats?.guild?.icon
        ? `https://cdn.discordapp.com/icons/${stats.guild.id}/${stats.guild.icon}.png`
        : null;

    return (
        <div className="min-h-screen bg-base-200">
            <Header>
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                    {/* Welcome */}
                    <div className="mb-8">
                        <h1 className="text-2xl font-semibold text-base-content">Welcome back, {user.username}</h1>
                        <p className="text-sm text-base-content/50 mt-1">Manage your Discord bot</p>
                    </div>

                    {/* Stats Row — Icon style */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                        {/* Bot Status */}
                        <div className="bg-base-100 rounded-lg border border-base-300 p-4">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-xs font-medium text-base-content/50 uppercase tracking-wider">
                                    <RobotIcon className="w-4 h-4 mr-2" aria-hidden="true" /> Status
                                </span>
                                <span className={`w-2 h-2 rounded-full ${stats?.bot_status === 'online' ? 'bg-success' : 'bg-base-content/20'`}></span>
                            </div>
                            <p className={`text-xl font-semibold ${stats?.bot_status === 'online' ? 'text-success' : 'text-base-content/40'`}>
                                {stats?.bot_status === 'online' ? 'Online' : 'Offline'}
                            </p>
                        </div>

                        {/* Members */}
                        <div className="bg-base-100 rounded-lg border border-base-300 p-4">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-xs font-medium text-base-content/50 uppercase tracking-wider">
                                    <UsersIcon className="w-4 h-4 mr-2" aria-hidden="true" /> Members
                                </span>
                            </div>
                            <p className="text-xl font-semibold text-base-content mt-3">{stats?.guild?.members || '—'}</p>
                        </div>

                        {/* Server */}
                        <div className="bg-base-100 rounded-lg border border-base-300 p-4">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-xs font-medium text-base-content/50 uppercase tracking-wider">
                                    <ServerIcon className="w-4 h-4 mr-2" aria-hidden="true" /> Server
                                </span>
                            </div>
                            <p className="text-xl font-semibold text-base-content mt-3 truncate">{stats?.guild?.name || '—'}</p>
                        </div>
                    </div>

                    {/* Server Info + Quick Links */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        {/* Server Card */}
                        <div className="lg:col-span-2 bg-base-100 rounded-lg border border-base-300 overflow-hidden">
                            <div className="h-24 bg-gradient-to-r from-primary/20 via-secondary/20 to-accent/20 relative">
                                {guildIconUrl && (
                                    <div className="absolute -bottom-8 left-6">
                                        <div className="avatar">
                                            <div className="w-16 h-16 rounded-xl ring-4 ring-base-100 bg-base-100 shadow-lg">
                                                <img src={guildIconUrl} alt={stats?.guild?.name} className="rounded-xl" />
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="p-6 pt-12">
                                <h2 className="text-lg font-semibold text-base-content">{stats?.guild?.name || 'Unknown Guild'}</h2>
                                <p className="text-xs text-base-content/40 mt-1">ID: {stats?.guild?.id || 'N/A'} · Region: {stats?.guild?.region || 'Classic'}</p>
                                {isAuthorizedUser && (
                                    <div className="mt-4">
                                        <Link href="/commands" className="btn btn-sm btn-primary">
                                            Manage Commands
                                        </Link>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Quick Links */}
                        <div className="bg-base-100 rounded-lg border border-base-300 p-4">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-xs font-medium text-base-content/50 uppercase tracking-wider">
                                    <ExternalLinkIcon className="w-4 h-4 mr-2" aria-hidden="true" /> Quick Links
                                </span>
                            </div>
                            <div className="mt-3 space-y-1">
                                <a href="https://discord.com" target="_blank" className="flex items-center justify-between px-3 py-2 text-sm text-base-content/70 hover:bg-base-200 rounded-md transition-colors">
                                    <span>Discord Support</span>
                                    <svg className="w-3.5 h-3.5 text-base-content/30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                                </a>
                                <a href="#" className="flex items-center justify-between px-3 py-2 text-sm text-base-content/70 hover:bg-base-200 rounded-md transition-colors">
                                    <span>Documentation</span>
                                    <svg className="w-3.5 h-3.5 text-base-content/30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </Header>
        </div>
    );
}