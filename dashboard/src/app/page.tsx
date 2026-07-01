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
      <div className="flex min-h-screen items-center justify-center pixel-page">
        <span className="loading loading-spinner loading-md text-primary"></span>
      </div>
    );
  }

  const isOnline = overview?.bot_status === 'online';
  const statusLabel = overview?.bot_status || 'checking';
  const memberLabel = overview?.guild?.members ? overview.guild.members.toLocaleString() : '---';

  const featureCards = [
    {
      title: 'Command control',
      description: 'Toggle bot commands with chunky switches.',
      icon: CommandLineIcon,
    },
    {
      title: 'Channel rules',
      description: 'Pixel-clear access rules for each room.',
      icon: ChatBubbleLeftRightIcon,
    },
    {
      title: 'Heartbeat watch',
      description: 'See when Mochi is awake or sleeping.',
      icon: BoltIcon,
    },
  ];

  return (
    <main className="min-h-screen pixel-page text-pink-950">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-5 py-6 sm:px-8 lg:px-10">
        <header className="flex items-center justify-between border-4 border-pink-950 bg-pink-200 px-4 py-3 shadow-[8px_8px_0_#8a174d]">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center border-4 border-pink-950 bg-pink-600 text-white shadow-[4px_4px_0_#8a174d]">
              <HeartIcon className="h-6 w-6" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-black uppercase tracking-wide">Mochi</p>
              <p className="text-xs font-bold uppercase text-pink-800">Pixel control center</p>
            </div>
          </div>

          <div className="hidden items-center gap-2 border-2 border-pink-950 bg-white px-3 py-1.5 text-xs font-black uppercase sm:flex">
            <span className={`h-3 w-3 border-2 border-pink-950 ${isOnline ? 'bg-emerald-400' : 'bg-amber-300'}`} />
            Bot {statusLabel}
          </div>
        </header>

        <section className="grid flex-1 items-center gap-8 py-10 lg:grid-cols-[1.05fr_0.95fr] lg:py-14">
          <div className="pixel-panel p-6 sm:p-8">
            <div className="mb-5 inline-flex items-center gap-2 border-2 border-pink-950 bg-white px-3 py-2 text-xs font-black uppercase text-pink-950 shadow-[4px_4px_0_#8a174d]">
              <SparklesIcon className="h-4 w-4" aria-hidden="true" />
              Sakura Pixel Dashboard
            </div>

            <h1 className="text-4xl font-black uppercase leading-none tracking-normal text-pink-950 sm:text-5xl lg:text-6xl">
              Manage Mochi in pink pixel mode.
            </h1>

            <p className="mt-5 max-w-2xl text-base font-bold leading-7 text-pink-900 sm:text-lg">
              A sharper arcade-style control room for Discord login, server status, commands, and channel rules.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
              <button onClick={login} className="pixel-button inline-flex min-h-14 items-center justify-center gap-2 px-6 text-base">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d={discordLogoPath} />
                </svg>
                Sign in with Discord
              </button>

              <div className="pixel-panel-soft px-5 py-3">
                <p className="text-xs font-black uppercase tracking-wide text-pink-800">Managing</p>
                <p className="mt-1 text-sm font-black text-pink-950">
                  {overview?.guild?.name || 'Loading server...'}
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="pixel-panel bg-white p-5">
              <div className="flex items-start justify-between gap-4 border-b-4 border-pink-950 pb-4">
                <div>
                  <p className="text-xs font-black uppercase tracking-wide text-pink-700">Live preview</p>
                  <h2 className="mt-2 text-2xl font-black uppercase text-pink-950">
                    {overview?.guild?.name || 'Mochi Server'}
                  </h2>
                </div>
                <div className={`pixel-chip px-3 py-1 ${isOnline ? 'bg-emerald-100' : 'bg-amber-100'}`}>
                  {isOnline ? 'Online' : 'Sleeping'}
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="pixel-panel-soft p-4">
                  <UsersIcon className="h-5 w-5 text-pink-700" aria-hidden="true" />
                  <p className="mt-4 text-2xl font-black text-pink-950">{memberLabel}</p>
                  <p className="text-xs font-black uppercase text-pink-800">Members</p>
                </div>
                <div className="pixel-panel-soft p-4">
                  <ShieldCheckIcon className="h-5 w-5 text-pink-700" aria-hidden="true" />
                  <p className="mt-4 text-2xl font-black text-pink-950">{overview?.guild?.region || 'Classic'}</p>
                  <p className="text-xs font-black uppercase text-pink-800">Region</p>
                </div>
              </div>

              <div className="mt-4 border-4 border-pink-950 bg-white p-4">
                <div className="flex items-center justify-between text-sm font-black uppercase">
                  <span>Heartbeat signal</span>
                  <span>{isOnline ? 'Healthy' : 'Waiting'}</span>
                </div>
                <div className="mt-3 h-4 border-2 border-pink-950 bg-pink-100">
                  <div className={`h-full ${isOnline ? 'w-[88%] bg-pink-600' : 'w-[34%] bg-amber-300'}`} />
                </div>
              </div>
            </div>

            <div className="grid gap-3">
              {featureCards.map((feature) => {
                const Icon = feature.icon;

                return (
                  <div key={feature.title} className="pixel-panel-soft flex items-center gap-3 bg-white px-4 py-3">
                    <div className="grid h-10 w-10 place-items-center border-2 border-pink-950 bg-pink-200 text-pink-800">
                      <Icon className="h-5 w-5" aria-hidden="true" />
                    </div>
                    <div>
                      <p className="text-sm font-black uppercase text-pink-950">{feature.title}</p>
                      <p className="text-xs font-bold text-pink-800">{feature.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
