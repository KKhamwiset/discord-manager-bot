'use client';

import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { statsApi, StatsOverview } from "@/lib/api";

export default function Home() {
  const { user, isLoading, login } = useAuth();
  const router = useRouter();
  const [overview, setOverview] = useState<StatsOverview | null>(null);

  useEffect(() => {
    if (!isLoading && user) { router.push('/dashboard'); }
  }, [user, isLoading, router]);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const data = await statsApi.getOverview();
        setOverview(data);
      } catch (error) {
        console.error("Failed to fetch bot overview:", error);
      }
    };
    fetchOverview();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-base-200">
        <span className="loading loading-spinner loading-md text-primary"></span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-base-200 flex items-center justify-center p-8">
      <div className="max-w-md w-full text-center">
        {/* Status Badge */}
        <div className="mb-8 flex justify-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-base-100 border border-base-300 rounded-full">
            <span className={`w-2 h-2 rounded-full ${overview?.bot_status === 'online' ? 'bg-success animate-pulse' : 'bg-base-content/20'}`}></span>
            <span className="text-xs font-medium text-base-content/60">
              Bot {overview?.bot_status || 'checking...'}
            </span>
          </div>
        </div>

        {/* Logo */}
        <div className="mb-6">
          <svg class="w-12 h-12 text-primary mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-semibold text-base-content mb-2">
          Mochi Dashboard
        </h1>
        <p className="text-base-content/50 mb-8">
          Discord bot management
        </p>

        {/* Server Info */}
        {overview?.guild?.name && (
          <div className="mb-8 p-4 bg-base-100 border border-base-300 rounded-lg">
            <p className="text-xs text-base-content/40 uppercase tracking-wider mb-1">Managing</p>
            <p className="text-base-content font-medium">{overview.guild.name}</p>
            {overview.guild.members && (
              <p className="text-sm text-base-content/50 mt-1">{overview.guild.members} members</p>
            )}
          </div>
        )}

        {/* Login Button */}
        <button onClick={login}
          className="btn btn-primary btn-lg w-full gap-3 text-base shadow-lg shadow-primary/10 hover:shadow-xl hover:shadow-primary/20 transition-all">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z" />
          </svg>
          Sign in with Discord
        </button>

        {/* Features */}
        <div className="mt-12 grid grid-cols-2 gap-3">
          <div className="p-4 bg-base-100 border border-base-300 rounded-lg text-center">
            <span className="text-xl"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg></span>
            <p className="text-xs font-medium text-base-content mt-2">Commands</p>
            <p className="text-xs text-base-content/40">Toggle on/off</p>
          </div>
          <div className="p-4 bg-base-100 border border-base-300 rounded-lg text-center">
            <span className="text-xl"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg></span>
            <p className="text-xs font-medium text-base-content mt-2">Channels</p>
            <p className="text-xs text-base-content/40">Manage access</p>
          </div>
        </div>
      </div>
    </div>
  );
}
