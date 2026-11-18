'use client';

import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import { authApi, statsApi, StatsOverview } from '@/lib/api';
import {
    ArrowTopRightOnSquareIcon,
    ChartBarIcon,
    CommandLineIcon,
    ServerIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function DashboardPage() {
    const { user, isLoading } = useAuth();
    const router = useRouter();
    const [stats, setStats] = useState<StatsOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadFailed, setLoadFailed] = useState(false);
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
                setLoadFailed(true);
            } finally {
                setLoading(false);
            }
        };

        void fetchData();
    }, []);

    if (isLoading || !user) {
        return (
            <div className="flex min-h-screen items-center justify-center pixel-page">
                <span className="loading loading-spinner loading-md text-primary" aria-label="Loading"></span>
            </div>
        );
    }

    const guild = stats?.guild;
    const guildIconUrl = guild?.id && guild?.icon
        ? `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`
        : null;

    const isOnline = stats?.bot_status === 'online';
    const status = loading
        ? { label: 'Checking', detail: 'Reading the bot status.', dot: 'bg-pink-400 animate-pulse' }
        : loadFailed
            ? { label: 'Unknown', detail: 'The API did not answer. Refresh to try again.', dot: 'bg-red-400' }
            : isOnline
                ? { label: 'Online', detail: 'Heartbeat received. Commands are answering.', dot: 'bg-emerald-400' }
                : { label: 'Sleeping', detail: 'No heartbeat in the last few minutes. Commands may not answer.', dot: 'bg-amber-300' };

    const actions = [
        {
            href: '/commands',
            label: 'Commands',
            description: isAuthorizedUser ? 'Turn commands on or off.' : 'See which commands are on.',
            icon: CommandLineIcon,
            enabled: true,
        },
        {
            href: '/channels',
            label: 'Channels',
            description: isAuthorizedUser
                ? 'Choose which commands work in each channel.'
                : 'Needs Manage Server permission.',
            icon: ChartBarIcon,
            enabled: isAuthorizedUser,
        },
        {
            href: 'https://discord.com/channels/@me',
            label: 'Open Discord',
            description: 'Opens in a new tab.',
            icon: ArrowTopRightOnSquareIcon,
            enabled: true,
            external: true,
        },
    ];

    return (
        <Header>
            <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
                <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <h1 className="text-3xl font-black uppercase text-pink-950 sm:text-4xl">Overview</h1>
                        <p className="mt-2 text-sm font-medium text-pink-900">
                            Bot health and the server Mochi manages.
                        </p>
                    </div>

                    <div className="pixel-panel-soft bg-white px-4 py-3" role="status">
                        <p className="flex items-center gap-2 text-sm font-black uppercase">
                            <span className={`h-3.5 w-3.5 border-2 border-pink-950 ${status.dot}`} aria-hidden="true" />
                            Bot {status.label}
                        </p>
                    </div>
                </div>

                <section className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr] lg:items-start">
                    <article className="pixel-panel overflow-hidden bg-white" aria-labelledby="server-name">
                        <div className="flex items-center gap-4 border-b-4 border-pink-950 bg-pink-300 p-5">
                            <div className="h-16 w-16 flex-shrink-0 border-4 border-pink-950 bg-white shadow-[4px_4px_0_#8a174d]">
                                {guildIconUrl ? (
                                    <img src={guildIconUrl} alt="" width={56} height={56} className="h-full w-full" />
                                ) : (
                                    <div className="grid h-full w-full place-items-center text-pink-700">
                                        <ServerIcon className="h-8 w-8" aria-hidden="true" />
                                    </div>
                                )}
                            </div>
                            <h2 id="server-name" className="min-w-0 break-words text-2xl font-black uppercase text-pink-950">
                                {loading ? (
                                    <span className="block h-7 w-48 animate-pulse bg-pink-200" aria-label="Loading server" />
                                ) : guild?.name || 'Server not found'}
                            </h2>
                        </div>

                        <dl className="grid divide-y-4 divide-pink-950 sm:grid-cols-2 sm:divide-x-4 sm:divide-y-0">
                            <div className="p-5">
                                <dt className="text-xs font-black uppercase text-pink-800">Members</dt>
                                <dd className="mt-2 text-3xl font-black tabular-nums text-pink-950">
                                    {guild?.members ? guild.members.toLocaleString() : '—'}
                                </dd>
                            </div>
                            <div className="p-5">
                                <dt className="text-xs font-black uppercase text-pink-800">Server ID</dt>
                                <dd className="mt-2 break-all text-sm font-bold tabular-nums text-pink-950">
                                    {guild?.id || '—'}
                                </dd>
                            </div>
                        </dl>

                        <div className="border-t-4 border-pink-950 bg-pink-100 p-5">
                            <p className="flex items-center gap-2 text-sm font-black uppercase text-pink-950">
                                <span className={`h-3.5 w-3.5 border-2 border-pink-950 ${status.dot}`} aria-hidden="true" />
                                Heartbeat: {status.label}
                            </p>
                            <p className="mt-1 text-sm font-medium text-pink-900">{status.detail}</p>
                        </div>
                    </article>

                    <aside className="pixel-panel bg-white p-5" aria-labelledby="actions-heading">
                        <h2 id="actions-heading" className="text-lg font-black uppercase text-pink-950">Go to</h2>
                        <div className="mt-4 space-y-3">
                            {actions.map((item) => {
                                const Icon = item.icon;
                                const content = (
                                    <>
                                        <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                                        <span>
                                            <span className="block text-sm">{item.label}</span>
                                            <span className="block text-xs font-medium normal-case text-pink-800">{item.description}</span>
                                        </span>
                                    </>
                                );
                                const rowClass = 'flex items-center gap-3 px-4 py-3';

                                if (!item.enabled) {
                                    return (
                                        <div
                                            key={item.label}
                                            aria-disabled="true"
                                            className={`${rowClass} border-3 border-dashed border-pink-800 bg-pink-50 font-black uppercase text-pink-800`}
                                        >
                                            {content}
                                        </div>
                                    );
                                }

                                return item.external ? (
                                    <a key={item.label} href={item.href} target="_blank" rel="noreferrer" className={`${rowClass} pixel-button-light`}>
                                        {content}
                                    </a>
                                ) : (
                                    <Link key={item.label} href={item.href} className={`${rowClass} pixel-button-light`}>
                                        {content}
                                    </Link>
                                );
                            })}
                        </div>
                    </aside>
                </section>
            </div>
        </Header>
    );
}
