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
                <span className="loading loading-spinner loading-md text-primary"></span>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-base-200">
            <Header>
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                    <div className="mb-6">
                        <h1 className="text-2xl font-semibold text-base-content">Channels</h1>
                        <p className="text-sm text-base-content/50 mt-1">Manage allowed channels for the bot</p>
                    </div>

                    {/* Table — Linear style */}
                    <div className="bg-base-100 rounded-lg border border-base-300 overflow-hidden">
                        <div className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-base-300 text-xs font-medium text-base-content/50 uppercase tracking-wider">
                            <div className="col-span-5">Channel</div>
                            <div className="col-span-2">Mode</div>
                            <div className="col-span-3">Allowed Commands</div>
                            <div className="col-span-2 text-right">Actions</div>
                        </div>

                        {loading ? (
                            [...Array(5)].map((_, i) => (
                                <div key={i} className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-base-300/50 animate-pulse">
                                    <div className="col-span-5"><div className="h-4 bg-base-200 rounded w-3/4"></div></div>
                                    <div className="col-span-2"><div className="h-4 bg-base-200 rounded w-1/2"></div></div>
                                    <div className="col-span-3"><div className="h-4 bg-base-200 rounded w-full"></div></div>
                                    <div className="col-span-2"><div className="h-4 bg-base-200 rounded w-1/2 ml-auto"></div></div>
                                </div>
                            ))
                        ) : channels.length > 0 ? (
                            channels.map(channel => (
                                <div key={channel.id} className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-base-300/50 hover:bg-base-200/30 transition-colors">
                                    <div className="col-span-5 flex items-center gap-3">
                                        <div className="w-8 h-8 bg-primary/10 rounded-md flex items-center justify-center text-primary flex-shrink-0">
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                                            </svg>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-base-content">{channel.name}</p>
                                            <p className="text-xs text-base-content/30 font-mono">{channel.id}</p>
                                        </div>
                                    </div>
                                    <div className="col-span-2 flex items-center">
                                        <span className={`badge badge-sm ${channel.cmd_mode === 'all' ? 'badge-success' : 'badge-primary'}`}>
                                            {channel.cmd_mode === 'all' ? 'All' : 'Whitelist'}
                                        </span>
                                    </div>
                                    <div className="col-span-3 flex items-center">
                                        {channel.cmd_mode === 'all' ? (
                                            <span className="text-sm text-base-content/30">All commands allowed</span>
                                        ) : (
                                            <div className="flex flex-wrap gap-1">
                                                {channel.allowed_commands.slice(0, 3).map(cmd => (
                                                    <span key={cmd} className="text-[10px] bg-base-200 text-base-content/50 px-2 py-0.5 rounded">{cmd}</span>
                                                ))}
                                                {channel.allowed_commands.length > 3 && (
                                                    <span className="text-[10px] text-base-content/30">+{channel.allowed_commands.length - 3}</span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                    <div className="col-span-2 flex items-center justify-end">
                                        <button
                                            onClick={() => handleChannelClick(channel)}
                                            className="btn btn-xs btn-ghost text-base-content/60 hover:text-base-content"
                                        >
                                            {channel.cmd_mode === 'all' ? 'View' : 'Manage'}
                                        </button>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="py-16 text-center">
                                <p className="text-base-content/40">No channels configured</p>
                            </div>
                        )}
                    </div>
                </div>
            </Header>

            <UnsavedChangesToast isOpen={pendingChanges.length > 0} onSave={handleSave} onDiscard={handleDiscard} loading={saving} />

            {/* Modal */}
            {selectedChannel && (
                <div className="modal modal-open">
                    <div className="modal-box max-w-xl bg-base-100 border border-base-300 shadow-2xl p-0">
                        {/* Modal Header */}
                        <div className="px-6 py-4 border-b border-base-300">
                            <h3 className="font-semibold text-base-content flex items-center gap-2">
                                <span className="text-primary">#</span> {selectedChannel.name}
                            </h3>
                            <p className="text-xs text-base-content/40 mt-1">
                                {selectedChannel.cmd_mode === 'all' ? 'All commands allowed' : 'Manage allowed commands'}
                            </p>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6">
                            {selectedChannel.cmd_mode === 'all' ? (
                                <div className="text-center py-8">
                                    <div className="text-4xl mb-3 text-success"><svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg></div>
                                    <p className="text-base-content font-medium">Unrestricted Access</p>
                                    <p className="text-sm text-base-content/40 mt-1">All commands are allowed in this channel.</p>
                                </div>
                            ) : (
                                <>
                                    <div className="mb-4">
                                        <label className="label">
                                            <span className="label-text text-xs font-medium text-base-content/50 uppercase tracking-wider">Allowed Commands</span>
                                        </label>
                                        <div className="flex flex-wrap gap-1.5 mt-2">
                                            {selectedChannel.allowed_commands.length > 0 ? (
                                                selectedChannel.allowed_commands.map(cmd => (
                                                    <div key={cmd} className="badge badge-primary badge-outline gap-1.5 px-3 py-1.5">
                                                        <span className="font-mono text-xs">{cmd}</span>
                                                        <button onClick={() => handleUpdateCommand(cmd, 'remove')} className="hover:text-error">
                                                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                                        </button>
                                                    </div>
                                                ))
                                            ) : (
                                                <p className="text-sm text-base-content/30 italic">No commands allowed yet.</p>
                                            )}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="label">
                                            <span className="label-text text-xs font-medium text-base-content/50 uppercase tracking-wider">Add Command</span>
                                        </label>
                                        <input type="text" className="input input-bordered w-full bg-base-200 text-sm mt-2" placeholder="Search commands..." value={commandSearch} onChange={(e) => setCommandSearch(e.target.value)} />
                                        <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-1.5 max-h-40 overflow-y-auto">
                                            {loadingCommands ? (
                                                [...Array(6)].map((_, i) => (<div key={i} className="h-8 bg-base-200 rounded animate-pulse"></div>))
                                            ) : filteredCommands.length > 0 ? (
                                                filteredCommands.slice(0, 12).map(cmd => (
                                                    <button key={cmd.name} onClick={() => handleUpdateCommand(cmd.name, 'add')}
                                                        className="btn btn-xs btn-ghost justify-start gap-1.5 border border-base-300 hover:border-primary hover:bg-primary/5 text-left">
                                                        <span className="font-mono text-xs truncate">{cmd.name}</span>
                                                        <span className="text-success text-xs">+</span>
                                                    </button>
                                                ))
                                            ) : (
                                                <div className="col-span-full text-center py-3 text-base-content/30 text-xs">No matching commands.</div>
                                            )}
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Modal Footer */}
                        <div className="px-6 py-4 border-t border-base-300 flex justify-end">
                            <button className="btn btn-sm" onClick={() => setSelectedChannel(null)}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
