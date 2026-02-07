'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { channelAPI, Channel } from '@/lib/api';
import Header from '@/components/Header';

export default function ChannelsPage() {
    const { user, token, isLoading } = useAuth();
    const router = useRouter();
    const [channels, setChannels] = useState<Channel[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/');
        }
    }, [user, isLoading, router]);

    useEffect(() => {
        const fetchData = async () => {
            if (!token) return;

            try {
                const data: any = await channelAPI.getChannel(token);
                if (data.channels) {
                    setChannels(data.channels);
                } else if (Array.isArray(data)) {
                    setChannels(data);
                } else {
                    setChannels([]);
                }
            } catch (error) {
                console.error('Failed to fetch channels:', error);
            } finally {
                setLoading(false);
            }
        };

        if (token) {
            fetchData();
        }
    }, [token]);

    if (isLoading || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen">
            <Header />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold mb-2">Allowed Channels</h2>
                    <p className="text-gray-400">Manage channels where the bot is allowed to operate.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                        [...Array(3)].map((_, i) => (
                            <div key={i} className="glass rounded-xl p-6 h-32 animate-pulse">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="w-10 h-10 bg-gray-800 rounded-lg" />
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 bg-gray-800 rounded w-3/4" />
                                        <div className="h-3 bg-gray-800 rounded w-1/2" />
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : channels.length > 0 ? (
                        channels.map(channel => (
                            <div key={channel.id} className="glass rounded-xl p-6 border border-gray-800 hover:border-purple-500/50 transition-all duration-300">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center text-purple-400">
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-lg text-white">{channel.name}</h4>
                                            <p className="text-xs text-gray-500 font-mono mt-1">ID: {channel.id}</p>
                                        </div>
                                    </div>
                                    <div className="px-2 py-1 rounded-md bg-green-500/10 text-green-400 text-xs font-bold uppercase">
                                        Active
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full py-12 text-center glass rounded-xl">
                            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-800 text-gray-600 mb-4">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-medium text-gray-300">No Allowed Channels Configured</h3>
                            <p className="text-gray-500 mt-1 max-w-md mx-auto">
                                The bot is currently not restricted to specific channels, or no channels have been allowed yet.
                            </p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
