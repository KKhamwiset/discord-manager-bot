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
    const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
    const [allCommands, setAllCommands] = useState<Command[]>([]);
    const [loadingCommands, setLoadingCommands] = useState(false);
    const [commandSearch, setCommandSearch] = useState('');
    const [pendingChanges, setPendingChanges] = useState<PendingChange[]>([]);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (!isLoading && !user) { router.push('/'); }
    }, [user, isLoading, router]);

    const fetchChannels = async () => {
        if (!token) return;
        try {
            const data: any = await channelAPI.getChannel(token);
            if (data.channels) { setChannels(data.channels); }
            else if (Array.isArray(data)) { setChannels(data); }
            else { setChannels([]); }
        } catch (error) {
            console.error('Failed to fetch channels:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchChannels(); }, [token]);

    const handleChannelClick = async (channel: Channel) => {
        setSelectedChannel(channel);
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
        setSelectedChannel(prev => prev ? {
            ...prev,
            allowed_commands: action === 'add'
                ? [...prev.allowed_commands, commandName]
                : prev.allowed_commands.filter(cmd => cmd !== commandName)
        } : null);
        setPendingChanges(prev => [...prev, { channelId: selectedChannel.id, command: commandName, action }]);
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
        setSelectedChannel(null);
    };

    const filteredCommands = allCommands.filter(cmd =>
        cmd.name.toLowerCase().includes(commandSearch.toLowerCase()) &&
        !selectedChannel?.allowed_commands.includes(cmd.name)
    );

    if (isLoading || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-base-200">
                <span className="loading loading-spinner loading-lg text-primary"></span>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-base-200">
            <Header>
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-base-content">Allowed Channels</h2>
                    <p className="text-base-content/60">Manage channels where the bot is allowed to operate.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                        [...Array(9)].map((_, i) => (
                            <div key={i} className="card bg-base-100 shadow-md border border-base-300 animate-pulse">
                                <div className="card-body p-6 h-32">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-base-300 rounded-lg"></div>
                                        <div className="flex-1 space-y-2">
                                            <div className="h-4 bg-base-300 rounded w-3/4"></div>
                                            <div className="h-3 bg-base-300 rounded w-1/2"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : channels.length > 0 ? (
                        channels.map(channel => (
                            <div key={channel.id} onClick={() => handleChannelClick(channel)}
                                className="card bg-base-100 shadow-md border border-base-300 hover:border-primary/50 hover:shadow-lg transition-all duration-300 cursor-pointer group hover:-translate-y-1">
                                <div className="card-body p-5">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                                                </svg>
                                            </div>
                                            <div>
                                                <h4 className="font-bold text-base-content group-hover:text-primary transition-colors">{channel.name}</h4>
                                                <p className="text-xs text-base-content/40 font-mono">ID: {channel.id}</p>
                                            </div>
                                        </div>
                                        <span className={`badge badge-sm ${channel.cmd_mode === 'all' ? 'badge-success' : 'badge-primary'}`}>
                                            {channel.cmd_mode === 'all' ? 'ALL' : `${channel.allowed_commands.length} Cmds`}
                                        </span>
                                    </div>
                                    {channel.cmd_mode !== 'all' && channel.allowed_commands.length > 0 && (
                                        <div className="mt-3 flex flex-wrap gap-1">
                                            {channel.allowed_commands.slice(0, 3).map(cmd => (
                                                <span key={cmd} className="text-[10px] bg-base-200 text-base-content/50 px-2 py-0.5 rounded">{cmd}</span>
                                            ))}
                                            {channel.allowed_commands.length > 3 && (
                                                <span className="text-[10px] bg-base-200 text-base-content/50 px-2 py-0.5 rounded">+{channel.allowed_commands.length - 3}</span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full">
                            <div className="text-center py-12 card bg-base-100 shadow-md border border-base-300">
                                <div className="card-body">
                                    <div className="text-5xl mb-4">📭</div>
                                    <h3 className="text-lg font-medium text-base-content">No Allowed Channels</h3>
                                    <p className="text-base-content/50 mt-1">The bot is not restricted to specific channels yet.</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </Header>

            <UnsavedChangesToast isOpen={pendingChanges.length > 0} onSave={handleSave} onDiscard={handleDiscard} loading={saving} />

            {/* Modal */}
            {selectedChannel && (
                <div className="modal modal-open">
                    <div className="modal-box max-w-2xl bg-base-100 border border-base-300 shadow-2xl">
                        <h3 className="font-bold text-lg text-base-content flex items-center gap-2">
                            <span className="text-primary">#</span> {selectedChannel.name}
                        </h3>
                        <p className="text-sm text-base-content/60 mt-1">
                            {selectedChannel.cmd_mode === 'all' ? "This channel allows ALL commands." : "Manage allowed commands for this channel"}
                        </p>

                        <div className="divider my-3"></div>

                        {selectedChannel.cmd_mode === 'all' ? (
                            <div className="text-center py-8">
                                <div className="text-5xl mb-4">✅</div>
                                <h4 className="text-lg font-medium text-base-content">Unrestricted Access</h4>
                                <p className="text-base-content/50 mt-1">This channel allows all commands.</p>
                            </div>
                        ) : (
                            <>
                                <div className="mb-4">
                                    <label className="label">
                                        <span className="label-text font-medium text-base-content">Allowed Commands</span>
                                    </label>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedChannel.allowed_commands.length > 0 ? (
                                            selectedChannel.allowed_commands.map(cmd => (
                                                <div key={cmd} className="badge badge-primary badge-outline gap-1 px-3 py-2">
                                                    <span className="font-mono text-sm">{cmd}</span>
                                                    <button onClick={() => handleUpdateCommand(cmd, 'remove')} className="hover:text-error">
                                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                                    </button>
                                                </div>
                                            ))
                                        ) : (
                                            <p className="text-sm text-base-content/40 italic">No commands allowed yet.</p>
                                        )}
                                    </div>
                                </div>

                                <div>
                                    <label className="label">
                                        <span className="label-text font-medium text-base-content">Add Command</span>
                                    </label>
                                    <input type="text" className="input input-bordered w-full bg-base-200" placeholder="Search commands to add..." value={commandSearch} onChange={(e) => setCommandSearch(e.target.value)} />

                                    <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
                                        {loadingCommands ? (
                                            [...Array(6)].map((_, i) => (<div key={i} className="h-10 bg-base-200 rounded-lg animate-pulse"></div>))
                                        ) : filteredCommands.length > 0 ? (
                                            filteredCommands.slice(0, 12).map(cmd => (
                                                <button key={cmd.name} onClick={() => handleUpdateCommand(cmd.name, 'add')}
                                                    className="btn btn-sm btn-ghost justify-start gap-2 border border-base-300 hover:border-primary hover:bg-primary/5 text-left">
                                                    <span className="font-mono text-xs truncate">{cmd.name}</span>
                                                    <span className="text-success">+</span>
                                                </button>
                                            ))
                                        ) : (
                                            <div className="col-span-full text-center py-4 text-base-content/40 text-sm">No matching commands.</div>
                                        )}
                                    </div>
                                </div>
                            </>
                        )}

                        <div className="modal-action mt-6">
                            <button className="btn" onClick={() => setSelectedChannel(null)}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
