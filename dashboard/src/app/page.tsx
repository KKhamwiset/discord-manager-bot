'use client';

import { useAuth } from '@/context/AuthContext';
import { statsApi, StatsOverview } from '@/lib/api';
import {
  BoltIcon,
  ChatBubbleLeftRightIcon,
  CommandLineIcon,
  HeartIcon,
  ShieldCheckIcon,
  SparklesIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

const discordLogoPath = `M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z`;

export default function Home() {
  const { user, isLoading, login } = useAuth();
  const router = useRouter();
  const [overview, setOverview] = useState<StatsOverview | null>(null);

  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const data = await statsApi.getOverview();
        setOverview(data);
      } catch (error) {
        console.error('Failed to fetch bot overview:', error);
      }
    };

    void fetchOverview();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[linear-gradient(180deg,#fff,#fff1f7)]">
        <span className="loading loading-spinner loading-md text-primary"></span>
      </div>
    );
  }

  const isOnline = overview?.bot_status === 'online';
  const statusLabel = overview?.bot_status || 'checking';
  const memberLabel = overview?.guild?.members
    ? overview.guild.members.toLocaleString()
    : '—';

  const featureCards = [
    {
      title: 'Command control',
      description: 'Toggle commands with a clean operator view.',
      icon: CommandLineIcon,
    },
    {
      title: 'Channel access',
      description: 'Keep bot usage scoped to the right places.',
      icon: ChatBubbleLeftRightIcon,
    },
    {
      title: 'Live heartbeat',
      description: 'See when Mochi is awake or sleeping.',
      icon: BoltIcon,
    },
  ];

  return (
    <main className="relative min-h-screen overflow-hidden bg-[linear-gradient(135deg,#fff_0%,#fff4fa_42%,#ffe7f2_100%)] text-base-content">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-pink-400 via-primary to-rose-400" />
      <div className="pointer-events-none absolute -left-28 top-16 h-96 w-96 rounded-full bg-pink-300/35 blur-[96px]" />
      <div className="pointer-events-none absolute left-1/2 top-1/3 h-80 w-80 -translate-x-1/2 rounded-full bg-white/80 blur-[72px]" />
      <div className="pointer-events-none absolute -right-24 bottom-10 h-[28rem] w-[28rem] rounded-full bg-rose-300/45 blur-[110px]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_28%_18%,rgba(255,255,255,0.92),transparent_24%),radial-gradient(circle_at_78%_28%,rgba(244,114,182,0.18),transparent_24%),radial-gradient(circle_at_45%_82%,rgba(251,207,232,0.36),transparent_28%)]" />

      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col px-5 py-6 sm:px-8 lg:px-10">
        <header className="flex items-center justify-between rounded-full border border-white/80 bg-white/72 px-4 py-3 shadow-[0_18px_60px_rgba(196,26,122,0.14)] ring-1 ring-pink-200/70 backdrop-blur-2xl sm:px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white shadow-lg shadow-pink-200">
              <HeartIcon className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-extrabold tracking-tight text-[#2a1220]">Mochi</p>
              <p className="text-xs font-semibold text-pink-700/80">Discord control center</p>
            </div>
          </div>

          <div className="hidden items-center gap-2 rounded-full border border-pink-200 bg-white/90 px-3 py-1.5 text-xs font-extrabold text-pink-900 shadow-sm sm:flex">
            <span className={`h-2.5 w-2.5 rounded-full ${isOnline ? 'bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.12)]' : 'bg-amber-400 shadow-[0_0_0_4px_rgba(251,191,36,0.14)]'}`} />
            Bot {statusLabel}
          </div>
        </header>

        <section className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[1.05fr_0.95fr] lg:py-16">
          <div className="max-w-3xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-pink-200 bg-white/88 px-4 py-2 text-sm font-extrabold text-pink-900 shadow-[0_12px_36px_rgba(196,26,122,0.12)] backdrop-blur-xl">
              <SparklesIcon className="h-4 w-4" aria-hidden="true" />
              Pink/white dashboard for Mochi Bot
            </div>

            <h1 className="text-5xl font-black leading-[0.95] tracking-[-0.06em] text-[#2a1220] sm:text-6xl lg:text-7xl">
              Manage Mochi with clearer, brighter control.
            </h1>

            <p className="mt-6 max-w-2xl text-lg font-medium leading-8 text-[#5c3147] sm:text-xl">
              A high-contrast Sakura landing page for Discord login, server status, and the fastest path into the bot dashboard.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <button
                onClick={login}
                className="btn btn-primary btn-lg min-h-14 rounded-2xl px-7 text-base font-extrabold shadow-xl shadow-pink-200/80 hover:-translate-y-0.5 hover:shadow-2xl hover:shadow-pink-200"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d={discordLogoPath} />
                </svg>
                Sign in with Discord
              </button>

              <div className="rounded-2xl border border-pink-200 bg-white/86 px-5 py-3 shadow-[0_14px_38px_rgba(196,26,122,0.12)] ring-1 ring-white/80 backdrop-blur-xl">
                <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-pink-800">Managing</p>
                <p className="mt-1 text-sm font-extrabold text-[#2a1220]">
                  {overview?.guild?.name || 'Loading server…'}
                </p>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute -inset-8 rounded-[2.75rem] bg-gradient-to-br from-pink-300/75 via-white/80 to-rose-300/75 blur-[44px]" />
            <div className="relative overflow-hidden rounded-[2rem] border border-white/80 bg-white/74 p-5 shadow-[0_34px_110px_rgba(196,26,122,0.24)] ring-1 ring-pink-200/80 backdrop-blur-2xl sm:p-6">
              <div className="rounded-[1.5rem] border border-pink-100/90 bg-gradient-to-br from-white via-pink-50/95 to-rose-50 p-5 shadow-inner shadow-white/70 ring-1 ring-white/90">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-extrabold uppercase tracking-[0.2em] text-pink-800">Live preview</p>
                    <h2 className="mt-2 text-2xl font-black tracking-tight text-[#2a1220]">{overview?.guild?.name || 'Mochi Server'}</h2>
                  </div>
                  <div className={`rounded-full border px-3 py-1 text-xs font-extrabold ${isOnline ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}>
                    {isOnline ? 'Online' : 'Sleeping'}
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3">
                  <div className="rounded-2xl border border-pink-200 bg-white p-4 shadow-[0_14px_38px_rgba(196,26,122,0.10)] ring-1 ring-white">
                    <UsersIcon className="h-5 w-5 text-primary" aria-hidden="true" />
                    <p className="mt-4 text-2xl font-black text-[#2a1220]">{memberLabel}</p>
                    <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-[#6b2447]">Members</p>
                  </div>
                  <div className="rounded-2xl border border-pink-200 bg-white p-4 shadow-[0_14px_38px_rgba(196,26,122,0.10)] ring-1 ring-white">
                    <ShieldCheckIcon className="h-5 w-5 text-primary" aria-hidden="true" />
                    <p className="mt-4 text-2xl font-black text-[#2a1220]">{overview?.guild?.region || 'Classic'}</p>
                    <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-[#6b2447]">Region</p>
                  </div>
                </div>

                <div className="mt-4 rounded-2xl border border-pink-200 bg-white p-4 shadow-[0_14px_38px_rgba(196,26,122,0.10)] ring-1 ring-white">
                  <div className="flex items-center justify-between text-sm font-bold text-[#2a1220]">
                    <span>Heartbeat signal</span>
                    <span>{isOnline ? 'Healthy' : 'Waiting'}</span>
                  </div>
                  <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-pink-100 ring-1 ring-pink-200/70">
                    <div className={`h-full rounded-full ${isOnline ? 'w-[88%] bg-gradient-to-r from-primary to-rose-400' : 'w-[34%] bg-gradient-to-r from-amber-300 to-pink-300'}`} />
                  </div>
                </div>
              </div>

              <div className="mt-4 grid gap-3">
                {featureCards.map((feature) => {
                  const Icon = feature.icon;

                  return (
                    <div key={feature.title} className="flex items-center gap-3 rounded-2xl border border-pink-200 bg-white/92 px-4 py-3 shadow-[0_14px_40px_rgba(196,26,122,0.10)] ring-1 ring-white/90 backdrop-blur-xl">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-pink-100 text-primary ring-1 ring-pink-200">
                        <Icon className="h-5 w-5" aria-hidden="true" />
                      </div>
                      <div>
                        <p className="text-sm font-extrabold text-[#2a1220]">{feature.title}</p>
                        <p className="text-xs font-semibold text-[#6b2447]">{feature.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

