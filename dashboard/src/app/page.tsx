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
        console.error("Failed to fetch bot overview:", error);
      }
    };
    fetchOverview();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-transparent to-cyan-900/20 pointer-events-none" />

      {/* Floating orbs */}
      <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />

      <div className="relative z-10 text-center max-w-2xl">
        {/* Bot Status Badge */}
        <div className="mb-6 flex justify-center">
          <div className="glass px-4 py-1.5 rounded-full flex items-center gap-2 border border-white/5">
            <div className={`w-2 h-2 rounded-full ${overview?.bot_status === 'online' ? 'bg-green-500 pulse-glow' : 'bg-gray-500'}`} />
            <span className="text-xs font-medium tracking-wider uppercase text-gray-300">
              Bot Status: {overview?.bot_status || 'Checking...'}
            </span>
          </div>
        </div>

        {/* Logo / Title */}
        <div className="mb-8">
          <h1 className="text-6xl font-bold mb-4 gradient-text">
            General เบ๊ Bot
          </h1>
          <p className="text-xl text-gray-400">
            Dashboard
          </p>
        </div>

        {/* Description */}
        <p className="text-gray-400 mb-12 text-lg leading-relaxed">
          Manage your Discord bot with a modern, intuitive dashboard.
          {overview?.guild?.name && (
            <span className="block mt-2 text-purple-400/80">
              Currently serving <b>{overview.guild.name}</b>
              {overview.guild.members && ` with ${overview.guild.members} members`}
            </span>
          )}
        </p>

        {/* Login Button */}
        <button
          onClick={login}
          className="group relative inline-flex items-center gap-3 px-8 py-4 bg-[#5865f2] hover:bg-[#4752c4] text-white font-semibold rounded-xl transition-all duration-200 hover:scale-105 hover:shadow-lg hover:shadow-[#5865f2]/25"
        >
          <svg
            className="w-6 h-6"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z" />
          </svg>
          Login with Discord
        </button>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass p-6 rounded-xl card-hover">
            <div className="w-12 h-12 bg-cyan-500/20 rounded-lg flex items-center justify-center mb-4 mx-auto">
              <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
            </div>
            <h3 className="font-semibold mb-2">Command Control</h3>
            <p className="text-sm text-gray-400">Enable or disable bot commands instantly</p>
          </div>

          <div className="glass p-6 rounded-xl card-hover">
            <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mb-4 mx-auto">
              <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="font-semibold mb-2">Secure Access</h3>
            <p className="text-sm text-gray-400">Discord OAuth2 authentication</p>
          </div>
        </div>
      </div>
    </main>
  );
}
