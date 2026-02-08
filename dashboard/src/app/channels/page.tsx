'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { channelAPI, Channel, commandsApi, Command } from '@/lib/api';
import Header from '@/components/Header';
import UnsavedChangesToast from '@/components/UnsavedChangesToast';

interface PendingChange {
    channelId: string;
    command: string;
    action: 'add' | 'remove';
}

export default function ChannelsPage() {
    const { user, token, isLoading } = useAuth();
    const router = useRouter();
    const [channels, setChannels] = useState<Channel[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal State
    const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [allCommands, setAllCommands] = useState<Command[]>([]);
    const [loadingCommands, setLoadingCommands] = useState(false);
    const [commandSearch, setCommandSearch] = useState('');

    // Pending Changes State
    const [pendingChanges, setPendingChanges] = useState<PendingChange[]>([]);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/');
        }
    }, [user, isLoading, router]);

    const fetchChannels = async () => {
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

    useEffect(() => {
        fetchChannels();
    }, [token]);

    const handleChannelClick = async (channel: Channel) => {
        setSelectedChannel(channel);
        setIsModalOpen(true);
        if (allCommands.length === 0 && channel.cmd_mode !== 'all') {
            setLoadingCommands(true);
            try {
                if (token) {
                    const data = await commandsApi.list(token);
                    setAllCommands(data.commands);
                }
            } catch (error) {
                console.error('Failed to fetch commands', error);
            } finally {
                setLoadingCommands(false);
            }
        }
    };

    const handleUpdateCommand = (commandName: string, action: 'add' | 'remove') => {
        if (!selectedChannel) return;

        // Optimistic update
        const updatedChannels = channels.map(c => {
            if (c.id === selectedChannel.id) {
                const newCommands = action === 'add'
                    ? [...c.allowed_commands, commandName]
                    : c.allowed_commands.filter(cmd => cmd !== commandName);
                return { ...c, allowed_commands: newCommands };
            }
            return c;
        });
        setChannels(updatedChannels);

        // Update selected channel state
        setSelectedChannel(prev => prev ? {
            ...prev,
            allowed_commands: action === 'add'
                ? [...prev.allowed_commands, commandName]
                : prev.allowed_commands.filter(cmd => cmd !== commandName)
        } : null);

        // Track pending change
        setPendingChanges(prev => [...prev, {
            channelId: selectedChannel.id,
            command: commandName,
            action
        }]);
    };

    const handleSave = async () => {
        if (!token || pendingChanges.length === 0) return;
        setSaving(true);
        try {
            await Promise.all(pendingChanges.map(change =>
                channelAPI.updateChannelCommand(token, change.channelId, change.command, change.action)
            ));

            setPendingChanges([]);
        } catch (error) {
            console.error('Failed to save changes:', error);
            await fetchChannels();
        } finally {
            setSaving(false);
        }
    };

    const handleDiscard = () => {
        setPendingChanges([]);
        fetchChannels();
        setIsModalOpen(false);
    };

    const filteredCommands = allCommands.filter(cmd =>
        cmd.name.toLowerCase().includes(commandSearch.toLowerCase()) &&
        !selectedChannel?.allowed_commands.includes(cmd.name)
    );

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

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold mb-2">Allowed Channels</h2>
                    <p className="text-gray-400">Manage channels where the bot is allowed to operate. Click on a channel to manage allowed commands.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                        [...Array(9)].map((_, i) => (
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
                            <div
                                key={channel.id}
                                onClick={() => handleChannelClick(channel)}
                                className="glass rounded-xl p-6 border border-gray-800 hover:border-purple-500/50 transition-all duration-300 cursor-pointer group relative overflow-hidden"
                            >
                                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <div className="flex items-start justify-between relative z-10">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-lg text-white group-hover:text-purple-400 transition-colors">{channel.name}</h4>
                                            <p className="text-xs text-gray-500 font-mono mt-1">ID: {channel.id}</p>
                                        </div>
                                    </div>
                                    <div className="px-2 py-1 rounded-md bg-green-500/10 text-green-400 text-xs font-bold uppercase flex items-center gap-1">
                                        {channel.cmd_mode === "all" ? (
                                            <>
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                                <span>ALL</span>
                                            </>
                                        ) : (
                                            `${channel.allowed_commands.length} Cmds`
                                        )}
                                    </div>
                                </div>
                                <div className="mt-4 flex flex-wrap gap-1 relative z-10">
                                    {channel.cmd_mode !== 'all' && (
                                        <>
                                            {channel.allowed_commands.slice(0, 3).map(cmd => (
                                                <span key={cmd} className="text-[10px] px-2 py-0.5 rounded-full bg-gray-800/50 text-gray-400 border border-gray-700/50">
                                                    {cmd}
                                                </span>
                                            ))}
                                            {channel.allowed_commands.length > 3 && (
                                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-800/50 text-gray-400 border border-gray-700/50">
                                                    +{channel.allowed_commands.length - 3}
                                                </span>
                                            )}
                                        </>
                                    )}
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

            <UnsavedChangesToast
                isOpen={pendingChanges.length > 0}
                onSave={handleSave}
                onDiscard={handleDiscard}
                loading={saving}
            />

            {/* Modal */}
            {isModalOpen && selectedChannel && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setIsModalOpen(false)}>
                    <div className="bg-[#0f0f13] border border-gray-800 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
                        <div className="p-6 border-b border-gray-800 flex items-center justify-between bg-gray-900/50">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <span className="text-purple-400">#</span> {selectedChannel.name}
                                </h3>
                                <p className="text-sm text-gray-400 mt-1">
                                    {selectedChannel.cmd_mode === 'all'
                                        ? "This channel allows ALL commands. Configuration is disabled."
                                        : "Manage allowed commands for this channel"}
                                </p>
                            </div>
                            <button
                                onClick={() => setIsModalOpen(false)}
                                className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="p-6 overflow-y-auto flex-1 custom-scrollbar">
                            {selectedChannel.cmd_mode === 'all' ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center">
                                    <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center text-green-500 mb-4">
                                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                    </div>
                                    <h4 className="text-lg font-medium text-white mb-2">Unrestricted Access</h4>
                                    <p className="text-gray-400 max-w-sm">
                                        This channel is configured to allow all commands. To restrict commands, update the configuration in your bot setup or database.
                                    </p>
                                </div>
                            ) : (
                                <>
                                    <div className="mb-6">
                                        <label className="block text-sm font-medium text-gray-300 mb-2">Allowed Commands</label>
                                        <div className="flex flex-wrap gap-2">
                                            {selectedChannel.allowed_commands.length > 0 ? (
                                                selectedChannel.allowed_commands.map(cmd => (
                                                    <div key={cmd} className="group flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 hover:bg-purple-500/20 transition-colors">
                                                        <span className="font-mono text-sm">{cmd}</span>
                                                        <button
                                                            onClick={() => handleUpdateCommand(cmd, 'remove')}
                                                            className="w-4 h-4 rounded-full flex items-center justify-center hover:bg-purple-500/30 text-purple-400/70 hover:text-purple-300 transition-colors"
                                                        >
                                                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                                            </svg>
                                                        </button>
                                                    </div>
                                                ))
                                            ) : (
                                                <p className="text-sm text-gray-500 italic py-2">No commands allowed yet. Add some below.</p>
                                            )}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">Add Command</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                                <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                                </svg>
                                            </div>
                                            <input
                                                type="text"
                                                className="w-full bg-gray-900/50 border border-gray-700 rounded-xl pl-10 pr-4 py-2.5 text-gray-200 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all placeholder-gray-600"
                                                placeholder="Search commands to add..."
                                                value={commandSearch}
                                                onChange={(e) => setCommandSearch(e.target.value)}
                                            />
                                        </div>

                                        <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2">
                                            {loadingCommands ? (
                                                [...Array(6)].map((_, i) => (
                                                    <div key={i} className="h-10 bg-gray-800/50 rounded-lg animate-pulse" />
                                                ))
                                            ) : filteredCommands.length > 0 ? (
                                                filteredCommands.slice(0, 12).map(cmd => (
                                                    <button
                                                        key={cmd.name}
                                                        onClick={() => handleUpdateCommand(cmd.name, 'add')}
                                                        className="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-800/30 border border-gray-700/50 hover:border-gray-600 hover:bg-gray-800/50 text-left transition-all group"
                                                    >
                                                        <span className="font-mono text-sm text-gray-300 group-hover:text-white truncate">{cmd.name}</span>
                                                        <svg className="w-4 h-4 text-gray-500 group-hover:text-green-400 opacity-0 group-hover:opacity-100 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                                        </svg>
                                                    </button>
                                                ))
                                            ) : (
                                                <div className="col-span-full text-center py-4 text-gray-500">
                                                    No matching commands found.
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
