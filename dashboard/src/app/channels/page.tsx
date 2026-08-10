'use client';

import Header from '@/components/Header';
import UnsavedChangesToast from '@/components/UnsavedChangesToast';
import { useAuth } from '@/context/AuthContext';
import { Channel, channelAPI, Command, commandsApi } from '@/lib/api';
import { HashtagIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';

interface PendingChange {
    channelId: string;
    command: string;
    action: 'add' | 'remove';
}

type AccessState = 'denied' | 'unavailable' | null;

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
    const [accessState, setAccessState] = useState<AccessState>(null);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/');
        }
    }, [user, isLoading, router]);

    const fetchChannels = useCallback(async () => {
        if (!token) return;

        try {
            const data = await channelAPI.getChannel(token);
            setChannels(Array.isArray(data) ? data : data.channels);
            setAccessState(null);
        } catch (error) {
            console.error('Failed to fetch channels:', error);
            const message = error instanceof Error ? error.message : '';
            setAccessState(message === 'Permission denied' ? 'denied' : 'unavailable');
            setSelectedChannel(null);
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        void fetchChannels();
    }, [fetchChannels]);

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

        const updatedChannels = channels.map((channel) => {
            if (channel.id !== selectedChannel.id) return channel;

            const allowedCommands = action === 'add'
                ? [...channel.allowed_commands, commandName]
                : channel.allowed_commands.filter((command) => command !== commandName);

            return { ...channel, allowed_commands: allowedCommands };
        });

        setChannels(updatedChannels);
        setSelectedChannel((prev) => {
            if (!prev) return null;

            const allowedCommands = action === 'add'
                ? [...prev.allowed_commands, commandName]
                : prev.allowed_commands.filter((command) => command !== commandName);

            return { ...prev, allowed_commands: allowedCommands };
        });
        setPendingChanges((prev) => [...prev, { channelId: selectedChannel.id, command: commandName, action }]);
    };

    const handleSave = async () => {
        if (!token || pendingChanges.length === 0) return;

        setSaving(true);
        try {
            await Promise.all(pendingChanges.map((change) => (
                channelAPI.updateChannelCommand(token, change.channelId, change.command, change.action)
            )));
            setPendingChanges([]);
        } catch (error) {
            console.error('Failed to save changes:', error);
            const message = error instanceof Error ? error.message : '';
            if (message === 'Permission denied' || message === 'Permission authority unavailable') {
                setAccessState(message === 'Permission denied' ? 'denied' : 'unavailable');
                setSelectedChannel(null);
            }
            await fetchChannels();
        } finally {
            setSaving(false);
        }
    };

    const handleDiscard = () => {
        setPendingChanges([]);
        void fetchChannels();
        setSelectedChannel(null);
    };

    const filteredCommands = allCommands.filter((command) => (
        command.name.toLowerCase().includes(commandSearch.toLowerCase())
        && !selectedChannel?.allowed_commands.includes(command.name)
    ));

    if (isLoading || !user) {
        return (
            <div className="flex min-h-screen items-center justify-center pixel-page">
                <span className="loading loading-spinner loading-md text-primary"></span>
            </div>
        );
    }

    return (
        <div className="min-h-screen pixel-page">
            <Header>
                <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
                    <div className="mb-6 pixel-panel p-5">
                        <div className="mb-3 inline-flex items-center gap-2 border-2 border-pink-950 bg-white px-3 py-1.5 text-xs font-black uppercase shadow-[3px_3px_0_#8a174d]">
                            <HashtagIcon className="h-4 w-4 text-pink-700" aria-hidden="true" />
                            Channel Map
                        </div>
                        <h1 className="text-3xl font-black uppercase text-pink-950">Channels</h1>
                        <p className="mt-1 text-sm font-bold text-pink-800">
                            Manage allowed command routes for each Discord channel.
                        </p>
                    </div>

                    {accessState ? (
                        <div className="pixel-panel bg-white px-6 py-14 text-center">
                            <p className="text-lg font-black uppercase text-pink-950">
                                {accessState === 'denied' ? 'Access denied' : 'Permission check unavailable'}
                            </p>
                            <p className="mx-auto mt-2 max-w-lg text-sm font-bold text-pink-800">
                                {accessState === 'denied'
                                    ? 'You need Manage Server permission to view or change channel configuration.'
                                    : 'Mochi could not verify your current Discord permissions. Please try again when the bot is available.'}
                            </p>
                        </div>
                    ) : (
                    <div className="pixel-panel overflow-hidden bg-white">
                        <div className="pixel-table-head grid grid-cols-12 gap-4 px-4 py-3">
                            <div className="col-span-5">Channel</div>
                            <div className="col-span-2">Mode</div>
                            <div className="col-span-3">Allowed</div>
                            <div className="col-span-2 text-right">Action</div>
                        </div>

                        {loading ? (
                            [...Array(5)].map((_, index) => (
                                <div key={index} className="pixel-row grid grid-cols-12 gap-4 px-4 py-4 animate-pulse">
                                    <div className="col-span-5"><div className="h-4 w-3/4 bg-pink-200"></div></div>
                                    <div className="col-span-2"><div className="h-4 w-1/2 bg-pink-200"></div></div>
                                    <div className="col-span-3"><div className="h-4 w-full bg-pink-200"></div></div>
                                    <div className="col-span-2"><div className="ml-auto h-4 w-1/2 bg-pink-200"></div></div>
                                </div>
                            ))
                        ) : channels.length > 0 ? (
                            channels.map((channel) => (
                                <div key={channel.id} className="pixel-row grid grid-cols-12 gap-4 px-4 py-4">
                                    <div className="col-span-5 flex min-w-0 items-center gap-3">
                                        <div className="grid h-9 w-9 flex-shrink-0 place-items-center border-2 border-pink-950 bg-pink-200">
                                            <HashtagIcon className="h-5 w-5 text-pink-800" aria-hidden="true" />
                                        </div>
                                        <div className="min-w-0">
                                            <p className="truncate text-sm font-black text-pink-950">{channel.name}</p>
                                            <p className="truncate text-xs font-bold text-pink-700">{channel.id}</p>
                                        </div>
                                    </div>
                                    <div className="col-span-2 flex items-center">
                                        <span className={`pixel-chip px-2 py-1 ${channel.cmd_mode === 'all' ? 'bg-emerald-100' : 'bg-pink-100'}`}>
                                            {channel.cmd_mode === 'all' ? 'All' : 'Whitelist'}
                                        </span>
                                    </div>
                                    <div className="col-span-3 flex items-center">
                                        {channel.cmd_mode === 'all' ? (
                                            <span className="text-sm font-bold text-pink-700">All commands</span>
                                        ) : (
                                            <div className="flex flex-wrap gap-1">
                                                {channel.allowed_commands.slice(0, 3).map((command) => (
                                                    <span key={command} className="border border-pink-950 bg-pink-100 px-2 py-0.5 text-[10px] font-black text-pink-950">
                                                        {command}
                                                    </span>
                                                ))}
                                                {channel.allowed_commands.length > 3 && (
                                                    <span className="text-[10px] font-black text-pink-700">+{channel.allowed_commands.length - 3}</span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                    <div className="col-span-2 flex items-center justify-end">
                                        <button onClick={() => handleChannelClick(channel)} className="pixel-button-light px-3 py-1 text-xs">
                                            {channel.cmd_mode === 'all' ? 'View' : 'Manage'}
                                        </button>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="py-16 text-center">
                                <p className="font-black uppercase text-pink-700">No channels configured</p>
                            </div>
                        )}
                    </div>
                    )}
                </div>
            </Header>

            <UnsavedChangesToast isOpen={pendingChanges.length > 0} onSave={handleSave} onDiscard={handleDiscard} loading={saving} />

            {selectedChannel && (
                <div className="modal modal-open">
                    <div className="modal-box max-w-xl rounded-none border-4 border-pink-950 bg-white p-0 shadow-[10px_10px_0_#8a174d]">
                        <div className="border-b-4 border-pink-950 bg-pink-200 px-6 py-4">
                            <h3 className="flex items-center gap-2 text-lg font-black uppercase text-pink-950">
                                <HashtagIcon className="h-5 w-5" aria-hidden="true" />
                                {selectedChannel.name}
                            </h3>
                            <p className="mt-1 text-xs font-bold uppercase text-pink-800">
                                {selectedChannel.cmd_mode === 'all' ? 'All commands allowed' : 'Manage allowed commands'}
                            </p>
                        </div>

                        <div className="p-6">
                            {selectedChannel.cmd_mode === 'all' ? (
                                <div className="py-8 text-center">
                                    <p className="text-lg font-black uppercase text-pink-950">Unrestricted Access</p>
                                    <p className="mt-1 text-sm font-bold text-pink-800">All commands are allowed in this channel.</p>
                                </div>
                            ) : (
                                <>
                                    <div className="mb-5">
                                        <p className="text-xs font-black uppercase text-pink-700">Allowed Commands</p>
                                        <div className="mt-3 flex flex-wrap gap-2">
                                            {selectedChannel.allowed_commands.length > 0 ? (
                                                selectedChannel.allowed_commands.map((command) => (
                                                    <div key={command} className="flex items-center gap-2 border-2 border-pink-950 bg-pink-100 px-3 py-1.5">
                                                        <span className="text-xs font-black text-pink-950">{command}</span>
                                                        <button onClick={() => handleUpdateCommand(command, 'remove')} className="text-pink-800 hover:text-red-600" aria-label={`Remove ${command}`}>
                                                            <XMarkIcon className="h-4 w-4" aria-hidden="true" />
                                                        </button>
                                                    </div>
                                                ))
                                            ) : (
                                                <p className="text-sm font-bold text-pink-500">No commands allowed yet.</p>
                                            )}
                                        </div>
                                    </div>

                                    <div>
                                        <p className="text-xs font-black uppercase text-pink-700">Add Command</p>
                                        <input
                                            type="text"
                                            className="mt-3 w-full pixel-input px-3 py-2 text-sm outline-none"
                                            placeholder="Search commands..."
                                            value={commandSearch}
                                            onChange={(event) => setCommandSearch(event.target.value)}
                                        />
                                        <div className="mt-4 grid max-h-44 grid-cols-2 gap-2 overflow-y-auto sm:grid-cols-3">
                                            {loadingCommands ? (
                                                [...Array(6)].map((_, index) => (
                                                    <div key={index} className="h-9 border-2 border-pink-950 bg-pink-100 animate-pulse"></div>
                                                ))
                                            ) : filteredCommands.length > 0 ? (
                                                filteredCommands.slice(0, 12).map((command) => (
                                                    <button
                                                        key={command.name}
                                                        onClick={() => handleUpdateCommand(command.name, 'add')}
                                                        className="flex items-center justify-between gap-2 border-2 border-pink-950 bg-white px-2 py-1.5 text-left text-xs font-black text-pink-950 hover:bg-pink-100"
                                                    >
                                                        <span className="truncate">{command.name}</span>
                                                        <PlusIcon className="h-4 w-4 text-pink-700" aria-hidden="true" />
                                                    </button>
                                                ))
                                            ) : (
                                                <div className="col-span-full py-3 text-center text-xs font-black uppercase text-pink-500">No matching commands.</div>
                                            )}
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>

                        <div className="flex justify-end border-t-4 border-pink-950 bg-pink-100 px-6 py-4">
                            <button className="pixel-button-light px-4 py-2 text-xs" onClick={() => setSelectedChannel(null)}>
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
