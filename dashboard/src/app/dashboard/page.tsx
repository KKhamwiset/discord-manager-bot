'use client';

import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import { authApi, statsApi, StatsOverview } from '@/lib/api';
import {
    ArrowTopRightOnSquareIcon,
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

type MetricTone = 'pink' | 'rose' | 'neutral';

type MetricCard = {
    label: string;
    value: string;
    detail: string;
    icon: typeof SparklesIcon;
    tone: MetricTone;
};

type ActionLink = {
    href: string;
    label: string;
    description: string;
    icon: typeof SparklesIcon;
    tone: 'primary' | 'secondary' | 'neutral';
    enabled: boolean;
    external?: boolean;
};

export default function DashboardPage() {
    const { user, isLoading, logout } = useAuth();
    const router = useRouter();
    const [stats, setStats] = useState<StatsOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [isAuthorizedUser, setIsAuthorizedUser] = useState(false);

    useEffect(() => {
        const getAuthData = async () => {
            const token = localStorage.getItem('auth_token');
            if (!token) return;

            try {
                const authData = await authApi.authorizedUser(token);
                setIsAuthorizedUser(authData.authorized);
            } catch (error) {
                console.error('Failed to get authorized user data:', error);
            }
        };

        void getAuthData();
    }, [user, logout]);

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
            <div className="min-h-screen flex items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(244,114,182,0.16),_transparent_34%),linear-gradient(180deg,_#fff,_#fff7fb_60%,_#ffffff)]">
                <span className="loading loading-spinner loading-md text-primary"></span>
            </div>
        );
    }

    const guildIconUrl = stats?.guild?.id && stats?.guild?.icon
        ? `https://cdn.discordapp.com/icons/${stats.guild.id}/${stats.guild.icon}.png`
        : null;

    const isOnline = stats?.bot_status === 'online';
    const statusLabel = loading ? 'Syncing…' : isOnline ? 'Online' : 'Sleeping';
    const statusBadgeClass = loading
        ? 'badge badge-neutral badge-outline'
        : isOnline
            ? 'badge badge-success badge-outline'
            : 'badge badge-warning badge-outline';
    const statusPillClass = loading
        ? 'text-pink-700 bg-pink-50 border-pink-100'
        : isOnline
            ? 'text-emerald-700 bg-emerald-50 border-emerald-100'
            : 'text-amber-700 bg-amber-50 border-amber-100';

    const metrics: MetricCard[] = [
        {
            label: 'Bot status',
            value: statusLabel,
            detail: isOnline
                ? 'Ready to respond to commands and keep things moving.'
                : 'Waiting for heartbeat, so the dashboard shows sleeping.',
            icon: SparklesIcon,
            tone: isOnline ? 'rose' : 'neutral',
        },
        {
            label: 'Members',
            value: stats?.guild?.members ? stats.guild.members.toLocaleString() : '—',
            detail: 'Discord guild member count from the overview API.',
            icon: UsersIcon,
            tone: 'pink',
        },
        {
            label: 'Server',
            value: stats?.guild?.name || '—',
            detail: stats?.guild?.id ? `Guild ID ${stats.guild.id}` : 'No guild data loaded yet.',
            icon: ServerIcon,
            tone: 'pink',
        },
        {
            label: 'Region',
            value: stats?.guild?.region || 'Classic',
            detail: 'Surface the guild metadata in a quick glance.',
            icon: ShieldCheckIcon,
            tone: 'neutral',
        },
    ];

    const actionLinks: ActionLink[] = [
        {
            href: '/commands',
            label: 'Manage commands',
            description: 'Enable, disable, and tune bot commands.',
            icon: CommandLineIcon,
            tone: 'primary',
            enabled: isAuthorizedUser,
        },
        {
            href: '/channels',
            label: 'Channel rules',
            description: 'Review command access by channel.',
            icon: ChartBarIcon,
            tone: 'secondary',
            enabled: isAuthorizedUser,
        },
        {
            href: 'https://discord.com',
            label: 'Open Discord',
            description: 'Jump back to the platform in a new tab.',
            icon: ArrowTopRightOnSquareIcon,
            tone: 'neutral',
            enabled: true,
            external: true,
        },
    ];
    const statusBullets = [
        'Pink/white palette tuned for quick scanning.',
        'Primary CTA only appears for authorized users.',
        'Server profile stays centered as the hero object.',
    ];

    return (
        <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(244,114,182,0.18),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(253,242,248,0.95),_transparent_24%),linear-gradient(180deg,_#ffffff_0%,_#fff7fb_52%,_#fff3f8_100%)]">
            <Header>
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8 lg:py-10">
                    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                        <div>
                            <div className="inline-flex items-center gap-2 rounded-full border border-pink-100 bg-white px-3 py-1 text-xs font-medium text-pink-700 shadow-sm">
                                <HeartIcon className="h-3.5 w-3.5" aria-hidden="true" />
                                Sakura control center
                            </div>
                            <h1 className="mt-4 text-3xl font-semibold tracking-tight text-base-content sm:text-4xl">
                                Mochi Bot Dashboard
                            </h1>
                            <p className="mt-2 max-w-2xl text-sm text-base-content/55 sm:text-base">
                                Pink-and-white command center for the bot, with a clean hierarchy for health, guild info, and quick actions.
                            </p>
                        </div>

                        <div className={`rounded-2xl border px-4 py-3 shadow-sm ${statusPillClass}`}>
                            <div className="flex items-center gap-2 text-sm font-semibold">
                                <span className={`h-2.5 w-2.5 rounded-full ${isOnline ? 'bg-emerald-500' : loading ? 'bg-pink-400 animate-pulse' : 'bg-amber-400'}`} />
                                {statusLabel}
                            </div>
                            <p className="mt-1 text-xs text-base-content/45">
                                {isOnline ? 'Heartbeat is healthy.' : loading ? 'Loading latest overview…' : 'Sleeping until heartbeat returns.'}
                            </p>
                        </div>
                    </div>

                    <section className="relative overflow-hidden rounded-[2rem] border border-pink-100/80 bg-white/90 p-6 shadow-[0_20px_80px_rgba(244,114,182,0.10)] backdrop-blur-xl sm:p-8">
                        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(135deg,rgba(244,114,182,0.08),transparent_36%,rgba(255,255,255,0.35))]" />
                        <div className="pointer-events-none absolute -right-20 top-0 h-56 w-56 rounded-full bg-pink-100/60 blur-3xl" />
                        <div className="relative grid gap-6 lg:grid-cols-[1.4fr_0.9fr] lg:items-center">
                            <div>
                                <div className="flex flex-wrap items-center gap-2 text-xs font-medium uppercase tracking-[0.22em] text-pink-500">
                                    <SparklesIcon className="h-4 w-4" aria-hidden="true" />
                                    Live overview
                                </div>
                                <h2 className="mt-4 max-w-2xl text-2xl font-semibold text-base-content sm:text-3xl">
                                    A softer, brighter control surface for Mochi Bot.
                                </h2>
                                <p className="mt-3 max-w-2xl text-sm leading-6 text-base-content/60 sm:text-base">
                                    The new layout keeps the theme soft and friendly: lots of white space, pink accents, rounded cards, and a strong path toward command management.
                                </p>

                                <div className="mt-5 flex flex-wrap gap-3">
                                    {isAuthorizedUser && (
                                        <Link href="/commands" className="btn btn-primary btn-sm sm:btn-md shadow-lg shadow-pink-200/70">
                                            <CommandLineIcon className="h-4 w-4" aria-hidden="true" />
                                            Manage Commands
                                        </Link>
                                    )}
                                    <Link href="/channels" className="btn btn-ghost btn-sm sm:btn-md border border-pink-100 bg-white text-pink-700 hover:bg-pink-50">
                                        <ChartBarIcon className="h-4 w-4" aria-hidden="true" />
                                        Channel Rules
                                    </Link>
                                </div>
                            </div>

                            <div className="grid gap-3 rounded-[1.5rem] border border-pink-100 bg-gradient-to-br from-pink-50 via-white to-rose-50 p-4 shadow-sm sm:p-5">
                                <div className="flex items-center justify-between">
                                    <span className="text-xs font-semibold uppercase tracking-[0.18em] text-base-content/45">
                                        Quick snapshot
                                    </span>
                                    <span className={statusBadgeClass}>{statusLabel}</span>
                                </div>
                                <div className="grid grid-cols-[auto_1fr] gap-4 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-pink-100">
                                    <div className="avatar">
                                        <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-pink-200 via-rose-100 to-white ring-4 ring-pink-50">
                                            {guildIconUrl ? (
                                                <img src={guildIconUrl} alt={stats?.guild?.name || 'Guild avatar'} />
                                            ) : (
                                                <div className="flex h-full w-full items-center justify-center text-pink-500">
                                                    <ServerIcon className="h-7 w-7" aria-hidden="true" />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-sm font-semibold text-base-content truncate">
                                            {stats?.guild?.name || 'Unknown Guild'}
                                        </p>
                                        <p className="mt-1 text-xs text-base-content/45 truncate">
                                            {stats?.guild?.id ? `ID ${stats.guild.id}` : 'Guild data loading…'}
                                        </p>
                                        <div className="mt-3 flex flex-wrap gap-2 text-xs">
                                            <span className="rounded-full bg-pink-50 px-2.5 py-1 text-pink-700 ring-1 ring-pink-100">
                                                {stats?.guild?.region || 'Classic'}
                                            </span>
                                            <span className="rounded-full bg-rose-50 px-2.5 py-1 text-rose-700 ring-1 ring-rose-100">
                                                {stats?.guild?.members ? `${stats.guild.members.toLocaleString()} members` : 'Members unknown'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                        {metrics.map((metric) => {
                            const Icon = metric.icon;
                            const toneClasses = {
                                pink: 'from-pink-50 to-white border-pink-100',
                                rose: 'from-rose-50 to-white border-rose-100',
                                neutral: 'from-white to-pink-50 border-base-200',
                            }[metric.tone];

                            return (
                                <article
                                    key={metric.label}
                                    className={`rounded-[1.5rem] border bg-gradient-to-br p-5 shadow-sm ${toneClasses}`}
                                >
                                    <div className="flex items-center justify-between gap-3">
                                        <div>
                                            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-base-content/40">
                                                {metric.label}
                                            </p>
                                            <p className="mt-3 text-lg font-semibold text-base-content break-words">
                                                {metric.value}
                                            </p>
                                        </div>
                                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-pink-100 text-pink-500">
                                            <Icon className="h-5 w-5" aria-hidden="true" />
                                        </div>
                                    </div>
                                    <p className="mt-3 text-sm leading-6 text-base-content/55">
                                        {metric.detail}
                                    </p>
                                </article>
                            );
                        })}
                    </section>

                    <section className="mt-6 grid gap-4 xl:grid-cols-[1.35fr_0.9fr]">
                        <article className="overflow-hidden rounded-[1.75rem] border border-pink-100 bg-white shadow-sm">
                            <div className="h-28 bg-gradient-to-r from-pink-100 via-white to-rose-100 relative">
                                <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-pink-200 to-transparent" />
                                <div className="absolute bottom-0 left-6 translate-y-1/2">
                                    <div className="rounded-3xl bg-white p-1 shadow-lg ring-1 ring-pink-100">
                                        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-pink-200 via-white to-rose-50 text-pink-500">
                                            <ServerIcon className="h-8 w-8" aria-hidden="true" />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="px-6 pb-6 pt-12 sm:px-8">
                                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                                    <div className="min-w-0">
                                        <h3 className="text-2xl font-semibold text-base-content truncate">
                                            {stats?.guild?.name || 'Unknown Guild'}
                                        </h3>
                                        <p className="mt-2 text-sm leading-6 text-base-content/55 max-w-2xl">
                                            A cleaner, softer home for server operations. The hero card keeps the guild identity visible while making the most common controls easy to reach.
                                        </p>
                                    </div>

                                    <div className="flex flex-wrap gap-2">
                                        <span className="badge badge-outline border-pink-200 text-pink-700 bg-pink-50">
                                            {isOnline ? 'Live' : loading ? 'Loading' : 'Sleeping'}
                                        </span>
                                        <span className="badge badge-outline border-rose-200 text-rose-700 bg-rose-50">
                                            {stats?.guild?.members ? `${stats.guild.members.toLocaleString()} members` : 'Members n/a'}
                                        </span>
                                    </div>
                                </div>

                                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                                    <div className="rounded-2xl border border-pink-100 bg-pink-50/60 p-4">
                                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-pink-600">
                                            Guild ID
                                        </p>
                                        <p className="mt-2 break-all text-sm font-medium text-base-content">
                                            {stats?.guild?.id || 'N/A'}
                                        </p>
                                    </div>
                                    <div className="rounded-2xl border border-pink-100 bg-white p-4">
                                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-base-content/45">
                                            Region
                                        </p>
                                        <p className="mt-2 text-sm font-medium text-base-content">
                                            {stats?.guild?.region || 'Classic'}
                                        </p>
                                    </div>
                                    <div className="rounded-2xl border border-pink-100 bg-rose-50/60 p-4">
                                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-rose-600">
                                            Bot status
                                        </p>
                                        <p className="mt-2 text-sm font-medium text-base-content">
                                            {statusLabel}
                                        </p>
                                    </div>
                                </div>

                                <div className="mt-6 rounded-2xl border border-pink-100 bg-gradient-to-r from-pink-50 to-white p-4">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-base-content">
                                        <SparklesIcon className="h-4 w-4 text-pink-500" aria-hidden="true" />
                                        Design notes
                                    </div>
                                    <ul className="mt-3 space-y-2 text-sm text-base-content/60">
                                        {statusBullets.map((bullet) => (
                                            <li key={bullet} className="flex items-start gap-2">
                                                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-pink-400" />
                                                <span>{bullet}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </article>

                        <aside className="space-y-4">
                            <article className="rounded-[1.75rem] border border-pink-100 bg-white p-5 shadow-sm">
                                <div className="flex items-center justify-between gap-3">
                                    <div>
                                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-base-content/40">
                                            Quick actions
                                        </p>
                                        <h3 className="mt-2 text-lg font-semibold text-base-content">
                                            One-click routes
                                        </h3>
                                    </div>
                                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-pink-50 text-pink-600 ring-1 ring-pink-100">
                                        <CommandLineIcon className="h-5 w-5" aria-hidden="true" />
                                    </div>
                                </div>

                                <div className="mt-5 space-y-3">
                                    {actionLinks.map((item) => {
                                        const Icon = item.icon;
                                        const disabled = !item.enabled;

                                        const content = (
                                            <>
                                                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-pink-50 text-pink-600 ring-1 ring-pink-100">
                                                    <Icon className="h-4 w-4" aria-hidden="true" />
                                                </div>
                                                <div className="min-w-0 flex-1">
                                                    <p className="text-sm font-semibold text-base-content truncate">
                                                        {item.label}
                                                    </p>
                                                    <p className="mt-1 text-xs leading-5 text-base-content/50">
                                                        {item.description}
                                                    </p>
                                                </div>
                                                <ArrowTopRightOnSquareIcon className="h-4 w-4 text-pink-300" aria-hidden="true" />
                                            </>
                                        );

                                        if (item.external) {
                                            return (
                                                <a
                                                    key={item.label}
                                                    href={item.href}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="flex items-center gap-3 rounded-2xl border border-pink-100 bg-gradient-to-r from-pink-50 to-white px-4 py-3 hover:shadow-sm hover:-translate-y-0.5"
                                                >
                                                    {content}
                                                </a>
                                            );
                                        }

                                        return (
                                            <Link
                                                key={item.label}
                                                href={item.href}
                                                aria-disabled={disabled}
                                                className={`flex items-center gap-3 rounded-2xl border px-4 py-3 hover:shadow-sm hover:-translate-y-0.5 ${
                                                    disabled
                                                        ? 'pointer-events-none cursor-not-allowed border-base-200 bg-base-100 opacity-50'
                                                        : 'border-pink-100 bg-gradient-to-r from-pink-50 to-white'
                                                }`}
                                            >
                                                {content}
                                            </Link>
                                        );
                                    })}
                                </div>
                            </article>

                            <article className="rounded-[1.75rem] border border-pink-100 bg-gradient-to-br from-white via-pink-50 to-rose-50 p-5 shadow-sm">
                                <div className="flex items-center justify-between gap-3">
                                    <div>
                                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-base-content/40">
                                            Health hint
                                        </p>
                                        <h3 className="mt-2 text-lg font-semibold text-base-content">
                                            Bot heartbeat
                                        </h3>
                                    </div>
                                    <div className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusPillClass}`}>
                                        {statusLabel}
                                    </div>
                                </div>

                                <div className="mt-5 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-pink-100">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="font-medium text-base-content">Connection signal</span>
                                        <span className="text-base-content/45">
                                            {isOnline ? 'Healthy' : loading ? 'Checking…' : 'Sleeping'}
                                        </span>
                                    </div>
                                    <div className="mt-3 h-2 rounded-full bg-pink-100/70 overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${isOnline ? 'w-[86%] bg-gradient-to-r from-pink-400 to-rose-400' : loading ? 'w-[50%] bg-gradient-to-r from-pink-300 to-pink-200 animate-pulse' : 'w-[30%] bg-gradient-to-r from-amber-300 to-pink-200'}`}
                                        />
                                    </div>
                                    <p className="mt-4 text-sm leading-6 text-base-content/60">
                                        {isOnline
                                            ? 'The dashboard is seeing a live heartbeat, so the bot should feel awake and ready.'
                                            : loading
                                                ? 'Awaiting the latest status snapshot from the API.'
                                                : 'No heartbeat currently detected, so the interface should reflect sleeping mode.'}
                                    </p>
                                </div>
                            </article>
                        </aside>
                    </section>
                </div>
            </Header>
        </div>
    );
}
