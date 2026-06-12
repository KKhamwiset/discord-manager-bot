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
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-base-200 via-base-100 to-secondary/10 flex flex-col items-center justify-center p-8">
      {/* Floating decorations */}
      <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/5 rounded-full blur-3xl pointer-events-none"></div>

      <div className="relative z-10 text-center max-w-2xl">
        {/* Status Badge */}
        <div className="mb-6 flex justify-center">
          <div className="badge badge-lg bg-base-100 border border-base-300 gap-2 px-4 py-3">
            <span className={`w-2 h-2 rounded-full ${overview?.bot_status === 'online' ? 'bg-success animate-pulse' : 'bg-base-content/20'}`}></span>
            <span className="text-sm font-medium text-base-content/70">
              Bot {overview?.bot_status || 'Checking...'}
            </span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text text-transparent">
          Mochi&apos;s Cozy Command Center 🌸
        </h1>
        <p className="text-xl text-base-content/60 mb-4">
          Cute Discord utility dashboard
        </p>
        <p className="text-base-content/50 mb-12 text-lg leading-relaxed">
          Manage your Discord bot with a cozy, intuitive dashboard.
          Let Mochi keep your server tidy and your day sparkling~ ✨
          {overview?.guild?.name && (
            <span className="block mt-2 text-primary/80">
              Currently serving <b>{overview.guild.name}</b>
              {overview.guild.members && ` with ${overview.guild.members} members`}
            </span>
          )}
        </p>

        {/* Login Button */}
        <button onClick={login}
          className="btn btn-primary btn-lg gap-3 text-lg px-8 shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 hover:scale-105 transition-all">
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z" />
          </svg>
          Login with Discord
        </button>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card bg-base-100 shadow-md border border-base-300 hover:shadow-lg hover:-translate-y-1 transition-all">
            <div className="card-body p-6 text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="card-title justify-center text-base-content">Command Control</h3>
              <p className="text-sm text-base-content/50">Enable or disable bot commands instantly</p>
            </div>
          </div>
          <div className="card bg-base-100 shadow-md border border-base-300 hover:shadow-lg hover:-translate-y-1 transition-all">
            <div className="card-body p-6 text-center">
              <div className="w-12 h-12 bg-success/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔒</span>
              </div>
              <h3 className="card-title justify-center text-base-content">Secure Access</h3>
              <p className="text-sm text-base-content/50">Discord OAuth2 authentication</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
