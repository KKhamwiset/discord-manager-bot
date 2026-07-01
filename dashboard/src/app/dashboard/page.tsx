'use client';

import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import { authApi, statsApi, StatsOverview } from '@/lib/api';
import {
    ArrowTopRightOnSquareIcon,
    BoltIcon,
    ChartBarIcon,
    CommandLineIcon,
    HeartIcon,
    ServerIcon,
    ShieldCheckIcon,
    SparklesIcon,
    UsersIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function DashboardPage() {
    const { user, isLoading } = useAuth();
    const router = useRouter();
    const [stats, setStats] = useState<StatsOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [isAuthorizedUser, setIsAuthorizedUser] = useState(false);

    useEffect(() => {
        let ignore = false;

        async function getAuthData() {
            const token = localStorage.getItem('auth_token');
            if (!token) return;

            try {
                const authData = await authApi.authorizedUser(token);
                if (!ignore) {
                    setIsAuthorizedUser(authData.authorized);
                }
            } catch (error) {
                console.error('Failed to get authorized user data:', error);
            }
        }

        void getAuthData();

        return () => {
            ignore = true;
        };
    }, [user]);

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

        void fetchData();
    }, []);

    if (isLoading || !user) {
        return (
            <div className="flex min-h-screen items-center justify-center pixel-page">
                <span className="loading loading-spinner loading-md text-primary"></span>
            </div>
        );
    }

    const guildIconUrl = stats?.guild?.id && stats?.guild?.icon
        ? `https://cdn.discordapp.com/icons/${stats.guild.id}/${stats.guild.icon}.png`
        : null;

    const isOnline = stats?.bot_status === 'online';
    const statusLabel = loading ? 'Syncing...' : isOnline ? 'Online' : 'Sleeping';

    const metrics = [
        {
            label: 'Bot status',
            value: statusLabel,
            detail: isOnline ? 'Commands are ready.' : 'Waiting for heartbeat.',
            icon: SparklesIcon,
        },
        {
            label: 'Members',
            value: stats?.guild?.members ? stats.guild.members.toLocaleString() : '---',
            detail: 'Guild member count.',
            icon: UsersIcon,
        },
        {
            label: 'Server',
            value: stats?.guild?.name || '---',
            detail: stats?.guild?.id ? `Guild ID ${stats.guild.id}` : 'No guild data yet.',
            icon: ServerIcon,
        },
        {
            label: 'Region',
            value: stats?.guild?.region || 'Classic',
            detail: 'Guild metadata snapshot.',
            icon: ShieldCheckIcon,
        },
    ];

    const actions = [
        {
            href: '/commands',
            label: 'Commands',
            description: 'Toggle command availability.',
            icon: CommandLineIcon,
            enabled: isAuthorizedUser,
        },
        {
            href: '/channels',
            label: 'Channels',
            description: 'Manage channel rule maps.',
            icon: ChartBarIcon,
            enabled: isAuthorizedUser,
        },
        {
            href: 'https://discord.com',
            label: 'Discord',
            description: 'Open Discord in a new tab.',
            icon: ArrowTopRightOnSquareIcon,
            enabled: true,
            external: true,
        },
    ];

    return (
        <Header>
            <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
                <div className="mb-6 grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end">
                    <div className="pixel-panel p-5">
                        <div className="mb-4 inline-flex items-center gap-2 border-2 border-pink-950 bg-white px-3 py-1.5 text-xs font-black uppercase shadow-[3px_3px_0_#8a174d]">
                            <HeartIcon className="h-4 w-4 text-pink-700" aria-hidden="true" />
                            Sakura Pixel Overview
                        </div>
                        <h1 className="text-3xl font-black uppercase text-pink-950 sm:text-4xl">
                            Mochi Bot Dashboard
                        </h1>
                        <p className="mt-2 max-w-2xl text-sm font-bold leading-6 text-pink-900">
                            A pink pixel-art control board for bot health, guild status, and fast operator actions.
                        </p>
                    </div>

                    <div className="pixel-panel-soft min-w-56 bg-white p-4">
                        <div className="flex items-center gap-2 text-sm font-black uppercase">
                            <span className={`h-4 w-4 border-2 border-pink-950 ${isOnline ? 'bg-emerald-400' : loading ? 'bg-pink-400 animate-pulse' : 'bg-amber-300'}`} />
                            {statusLabel}
                        </div>
                        <p className="mt-2 text-xs font-bold uppercase text-pink-800">
                            {isOnline ? 'Heartbeat healthy' : loading ? 'Reading signal' : 'Sleeping mode'}
                        </p>
                    </div>
                </div>

                <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    {metrics.map((metric) => {
                        const Icon = metric.icon;

                        return (
                            <article key={metric.label} className="pixel-panel-soft bg-white p-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div className="min-w-0">
                                        <p className="text-xs font-black uppercase text-pink-700">{metric.label}</p>
                                        <p className="mt-3 break-words text-lg font-black text-pink-950">{metric.value}</p>
                                    </div>
                                    <div className="grid h-10 w-10 place-items-center border-2 border-pink-950 bg-pink-200">
                                        <Icon className="h-5 w-5 text-pink-800" aria-hidden="true" />
                                    </div>
                                </div>
                                <p className="mt-3 text-xs font-bold leading-5 text-pink-800">{metric.detail}</p>
                            </article>
                        );
                    })}
                </section>

                <section className="mt-6 grid gap-5 xl:grid-cols-[1.35fr_0.85fr]">
                    <article className="pixel-panel overflow-hidden bg-white">
                        <div className="border-b-4 border-pink-950 bg-pink-300 p-5">
                            <div className="flex items-center gap-4">
                                <div className="h-16 w-16 border-4 border-pink-950 bg-white shadow-[4px_4px_0_#8a174d]">
                                    {guildIconUrl ? (
                                        <img src={guildIconUrl} alt={stats?.guild?.name || 'Guild avatar'} />
                                    ) : (
                                        <div className="grid h-full w-full place-items-center text-pink-700">
                                            <ServerIcon className="h-8 w-8" aria-hidden="true" />
                                        </div>
                                    )}
                                </div>
                                <div className="min-w-0">
                                    <p className="text-xs font-black uppercase text-pink-800">Server card</p>
                                    <h2 className="truncate text-2xl font-black uppercase text-pink-950">
                                        {stats?.guild?.name || 'Unknown Guild'}
                                    </h2>
                                </div>
                            </div>
                        </div>

                        <div className="grid gap-4 p-5 sm:grid-cols-3">
                            <div className="border-4 border-pink-950 bg-pink-100 p-4">
                                <p className="text-xs font-black uppercase text-pink-700">Guild ID</p>
                                <p className="mt-2 break-all text-sm font-bold text-pink-950">{stats?.guild?.id || 'N/A'}</p>
                            </div>
                            <div className="border-4 border-pink-950 bg-white p-4">
                                <p className="text-xs font-black uppercase text-pink-700">Region</p>
                                <p className="mt-2 text-sm font-bold text-pink-950">{stats?.guild?.region || 'Classic'}</p>
                            </div>
                            <div className="border-4 border-pink-950 bg-pink-100 p-4">
                                <p className="text-xs font-black uppercase text-pink-700">Bot</p>
                                <p className="mt-2 text-sm font-bold text-pink-950">{statusLabel}</p>
                            </div>
                        </div>

                        <div className="border-t-4 border-pink-950 p-5">
                            <div className="flex items-center gap-2 text-sm font-black uppercase">
                                <BoltIcon className="h-5 w-5 text-pink-700" aria-hidden="true" />
                                Heartbeat signal
                            </div>
                            <div className="mt-3 h-5 border-4 border-pink-950 bg-pink-100">
                                <div className={`h-full ${isOnline ? 'w-[86%] bg-pink-600' : loading ? 'w-[50%] bg-pink-400 animate-pulse' : 'w-[30%] bg-amber-300'}`} />
                            </div>
                        </div>
                    </article>

                    <aside className="space-y-5">
                        <article className="pixel-panel bg-white p-5">
                            <h3 className="text-lg font-black uppercase text-pink-950">Quick actions</h3>
                            <div className="mt-4 space-y-3">
                                {actions.map((item) => {
                                    const Icon = item.icon;
                                    const disabled = !item.enabled;
                                    const className = disabled
                                        ? 'pointer-events-none opacity-50'
                                        : item.external
                                            ? 'pixel-button-light'
                                            : 'pixel-button-light';

                                    const content = (
                                        <>
                                            <Icon className="h-5 w-5" aria-hidden="true" />
                                            <span>
                                                <span className="block text-sm">{item.label}</span>
                                                <span className="block text-[10px] normal-case text-pink-700">{item.description}</span>
                                            </span>
                                        </>
                                    );

                                    return item.external ? (
                                        <a key={item.label} href={item.href} target="_blank" rel="noreferrer" className={`flex items-center gap-3 px-4 py-3 ${className}`}>
                                            {content}
                                        </a>
                                    ) : (
                                        <Link key={item.label} href={item.href} className={`flex items-center gap-3 px-4 py-3 ${className}`}>
                                            {content}
                                        </Link>
                                    );
                                })}
                            </div>
                        </article>

                        <article className="pixel-panel-soft bg-pink-100 p-5">
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <p className="text-xs font-black uppercase text-pink-700">Mode</p>
                                    <h3 className="mt-1 text-lg font-black uppercase text-pink-950">Pixel Sakura</h3>
                                </div>
                                <SparklesIcon className="h-7 w-7 text-pink-700" aria-hidden="true" />
                            </div>
                            <p className="mt-4 text-sm font-bold leading-6 text-pink-900">
                                Square controls, pink panels, heavy outlines, and simple scan-first operator content.
                            </p>
                        </article>
                    </aside>
                </section>
            </div>
        </Header>
    );
}
