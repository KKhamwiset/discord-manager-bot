'use client';

import Header from '@/components/Header';
import UnsavedChangesToast from '@/components/UnsavedChangesToast';
import { useAuth } from '@/context/AuthContext';
import { Channel, channelAPI, Command, commandsApi } from '@/lib/api';
import { HashtagIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';

interface PendingChange {
    channelId: string;
    command: string;
    action: 'add' | 'remove';
}

type AccessState = 'denied' | 'unavailable' | null;

const VISIBLE_ALLOWED = 3;

export default function ChannelsPage() {
    const { user, token, isLoading } = useAuth();
    const router = useRouter();
    const dialogRef = useRef<HTMLDialogElement>(null);
    const [channels, setChannels] = useState<Channel[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
    const [allCommands, setAllCommands] = useState<Command[]>([]);
    const [loadingCommands, setLoadingCommands] = useState(false);
    const [commandSearch, setCommandSearch] = useState('');
    const [pendingChanges, setPendingChanges] = useState<PendingChange[]>([]);
    const [saving, setSaving] = useState(false);
    const [accessState, setAccessState] = useState<AccessState>(null);
    const [saveError, setSaveError] = useState<string | null>(null);

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

    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) return;
        if (selectedChannel && !dialog.open) {
            dialog.showModal();
        } else if (!selectedChannel && dialog.open) {
            dialog.close();
        }
    }, [selectedChannel]);

    const closeDialog = () => {
        setSelectedChannel(null);
        setCommandSearch('');
    };

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

        const apply = (channel: Channel): Channel => ({
            ...channel,
            allowed_commands: action === 'add'
                ? [...channel.allowed_commands, commandName]
                : channel.allowed_commands.filter((command) => command !== commandName),
        });

        setChannels((prev) => prev.map((channel) => (channel.id === selectedChannel.id ? apply(channel) : channel)));
        setSelectedChannel((prev) => (prev ? apply(prev) : null));
        setPendingChanges((prev) => {
            // Adding then removing the same command cancels out; sending both
            // in parallel could land in either order on the server.
            const opposite = prev.findIndex((change) => (
                change.channelId === selectedChannel.id
                && change.command === commandName
                && change.action !== action
            ));
            if (opposite !== -1) {
                return prev.filter((_, index) => index !== opposite);
            }
            return [...prev, { channelId: selectedChannel.id, command: commandName, action }];
        });
    };

    const handleSave = async () => {
        if (!token || pendingChanges.length === 0) return;

        setSaving(true);
        setSaveError(null);
        const results = await Promise.allSettled(pendingChanges.map((change) => (
            channelAPI.updateChannelCommand(token, change.channelId, change.command, change.action)
        )));
        const failures = results.filter((result): result is PromiseRejectedResult => result.status === 'rejected');

        if (failures.length > 0) {
            const message = failures[0].reason instanceof Error ? failures[0].reason.message : '';
            console.error('Failed to save changes:', failures);
            if (message === 'Permission denied' || message === 'Permission authority unavailable') {
                setAccessState(message === 'Permission denied' ? 'denied' : 'unavailable');
                setSelectedChannel(null);
            } else {
                setSaveError(`${failures.length} of ${pendingChanges.length} changes were not saved. The list now shows what is saved; try those changes again.`);
            }
        }

        setPendingChanges([]);
        await fetchChannels();
        setSaving(false);
    };

    const handleDiscard = () => {
        setPendingChanges([]);
        setSaveError(null);
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
                <span className="loading loading-spinner loading-md text-primary" aria-label="Loading"></span>
            </div>
        );
    }

    return (
        <>
            <Header>
                <div className="mx-auto max-w-6xl px-4 py-8 pb-32 sm:px-6">
                    <div className="mb-6 pixel-panel p-5">
                        <h1 className="text-3xl font-black uppercase text-pink-950">Channels</h1>
                        <p className="mt-1 text-sm font-medium text-pink-900">
                            Choose which commands work in each channel. Changes apply after you save.
                        </p>
                    </div>

                    {saveError && (
                        <div role="alert" className="mb-4 flex items-center justify-between gap-3 border-2 border-red-950 bg-red-100 p-3 text-sm font-bold text-red-900 shadow-[3px_3px_0_#8a174d]">
                            <span>{saveError}</span>
                            <button
                                onClick={() => setSaveError(null)}
                                className="flex-shrink-0 font-black uppercase underline underline-offset-2 hover:text-red-700"
                            >
                                Dismiss
                            </button>
                        </div>
                    )}

                    {accessState ? (
                        <div className="pixel-panel bg-white px-6 py-14 text-center" role="alert">
                            <p className="text-lg font-black uppercase text-pink-950">
                                {accessState === 'denied' ? 'Access denied' : 'Permission check unavailable'}
                            </p>
                            <p className="mx-auto mt-2 max-w-lg text-sm font-medium text-pink-900">
                                {accessState === 'denied'
                                    ? 'You need Manage Server permission to view or change channel configuration.'
                                    : 'Mochi could not verify your current Discord permissions. Please try again when the bot is available.'}
                            </p>
                        </div>
                    ) : (
                        <div className="pixel-panel overflow-hidden bg-white">
                            <div className="pixel-table-head hidden grid-cols-12 gap-4 px-4 py-3 md:grid">
                                <div className="col-span-5">Channel</div>
                                <div className="col-span-2">Mode</div>
                                <div className="col-span-3">Allowed</div>
                                <div className="col-span-2 text-right">Action</div>
                            </div>

                            {loading ? (
                                [...Array(5)].map((_, index) => (
                                    <div key={index} className="pixel-row grid grid-cols-[1fr_auto] gap-3 px-4 py-4 animate-pulse md:grid-cols-12 md:gap-4">
                                        <div className="md:col-span-5"><div className="h-4 w-3/4 bg-pink-200"></div></div>
                                        <div className="hidden md:col-span-2 md:block"><div className="h-4 w-1/2 bg-pink-200"></div></div>
                                        <div className="hidden md:col-span-3 md:block"><div className="h-4 w-full bg-pink-200"></div></div>
                                        <div className="md:col-span-2"><div className="ml-auto h-4 w-16 bg-pink-200"></div></div>
                                    </div>
                                ))
                            ) : channels.length > 0 ? (
                                channels.map((channel) => {
                                    const isOpen = channel.cmd_mode === 'all';
                                    const extra = channel.allowed_commands.length - VISIBLE_ALLOWED;

                                    return (
                                        <div key={channel.id} className="pixel-row grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-2 px-4 py-4 md:grid-cols-12 md:gap-4">
                                            <div className="flex min-w-0 items-center gap-3 md:col-span-5">
                                                <div className="grid h-9 w-9 flex-shrink-0 place-items-center border-2 border-pink-950 bg-pink-200">
                                                    <HashtagIcon className="h-5 w-5 text-pink-800" aria-hidden="true" />
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="truncate text-sm font-black text-pink-950" title={channel.name}>{channel.name}</p>
                                                    <p className="truncate text-xs font-bold tabular-nums text-pink-800">{channel.id}</p>
                                                </div>
                                            </div>
                                            <div className="col-span-2 row-start-2 flex items-center md:row-start-auto">
                                                <span className={`pixel-chip px-2 py-1 ${isOpen ? 'bg-emerald-100' : 'bg-pink-100'}`}>
                                                    {isOpen ? 'All commands' : 'Allow list'}
                                                </span>
                                            </div>
                                            <div className="col-span-2 row-start-3 flex items-center md:col-span-3 md:row-start-auto">
                                                {isOpen ? (
                                                    <span className="text-sm font-medium text-pink-900">Every command works here</span>
                                                ) : channel.allowed_commands.length === 0 ? (
                                                    <span className="text-sm font-medium italic text-pink-800">No commands allowed</span>
                                                ) : (
                                                    <div className="flex flex-wrap items-center gap-1">
                                                        {channel.allowed_commands.slice(0, VISIBLE_ALLOWED).map((command) => (
                                                            <span key={command} className="border border-pink-950 bg-pink-100 px-2 py-0.5 text-xs font-black text-pink-950">
                                                                {command}
                                                            </span>
                                                        ))}
                                                        {extra > 0 && (
                                                            <span className="text-xs font-black text-pink-800">+{extra} more</span>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="col-start-2 row-start-1 flex items-center justify-end md:col-span-2 md:col-start-auto md:row-start-auto">
                                                <button
                                                    onClick={() => handleChannelClick(channel)}
                                                    className="pixel-button-light px-3 py-1 text-xs"
                                                    aria-label={`${isOpen ? 'View' : 'Edit'} commands for #${channel.name}`}
                                                >
                                                    {isOpen ? 'View' : 'Edit'}
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })
                            ) : (
                                <div className="px-6 py-16 text-center">
                                    <p className="font-black uppercase text-pink-950">No channels configured</p>
                                    <p className="mt-1 text-sm font-medium text-pink-900">Channels appear here once Mochi has a rule for them.</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </Header>

            <UnsavedChangesToast
                isOpen={pendingChanges.length > 0}
                count={pendingChanges.length}
                onSave={handleSave}
                onDiscard={handleDiscard}
                loading={saving}
            />

            <dialog ref={dialogRef} className="modal" onClose={closeDialog} aria-labelledby="channel-dialog-title">
                {selectedChannel && (
                    <div className="modal-box max-w-xl rounded-none border-4 border-pink-950 bg-white p-0 shadow-[10px_10px_0_#8a174d]">
                        <div className="flex items-start justify-between gap-4 border-b-4 border-pink-950 bg-pink-200 px-6 py-4">
                            <div className="min-w-0">
                                <h2 id="channel-dialog-title" className="flex items-center gap-2 text-lg font-black uppercase text-pink-950">
                                    <HashtagIcon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                                    <span className="truncate">{selectedChannel.name}</span>
                                </h2>
                                <p className="mt-1 text-sm font-medium text-pink-900">
                                    {selectedChannel.cmd_mode === 'all'
                                        ? 'Every command works in this channel.'
                                        : 'Only the commands below work in this channel.'}
                                </p>
                            </div>
                            <button
                                onClick={closeDialog}
                                className="grid h-9 w-9 flex-shrink-0 place-items-center border-2 border-pink-950 bg-white text-pink-950 hover:bg-pink-100"
                                aria-label="Close"
                            >
                                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                            </button>
                        </div>

                        {selectedChannel.cmd_mode !== 'all' && (
                            <div className="p-6">
                                <h3 className="text-xs font-black uppercase text-pink-800">
                                    Allowed ({selectedChannel.allowed_commands.length})
                                </h3>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {selectedChannel.allowed_commands.length > 0 ? (
                                        selectedChannel.allowed_commands.map((command) => (
                                            <div key={command} className="flex items-center gap-1 border-2 border-pink-950 bg-pink-100 py-1 pl-3 pr-1">
                                                <span className="text-xs font-black text-pink-950">{command}</span>
                                                <button
                                                    onClick={() => handleUpdateCommand(command, 'remove')}
                                                    className="grid h-7 w-7 place-items-center text-pink-800 hover:bg-pink-200 hover:text-red-700"
                                                    aria-label={`Remove ${command}`}
                                                >
                                                    <XMarkIcon className="h-4 w-4" aria-hidden="true" />
                                                </button>
                                            </div>
                                        ))
                                    ) : (
                                        <p className="text-sm font-medium italic text-pink-800">No commands allowed yet. Add one below.</p>
                                    )}
                                </div>

                                <label htmlFor="command-search" className="mt-6 block text-xs font-black uppercase text-pink-800">
                                    Add a command
                                </label>
                                <input
                                    id="command-search"
                                    type="search"
                                    autoComplete="off"
                                    className="mt-3 w-full pixel-input px-3 py-2 text-sm outline-none"
                                    placeholder="Search by name"
                                    value={commandSearch}
                                    onChange={(event) => setCommandSearch(event.target.value)}
                                />
                                <div className="mt-4 grid max-h-44 grid-cols-2 gap-2 overflow-y-auto p-0.5 sm:grid-cols-3">
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
                                                aria-label={`Allow ${command.name}`}
                                            >
                                                <span className="truncate">{command.name}</span>
                                                <PlusIcon className="h-4 w-4 flex-shrink-0 text-pink-800" aria-hidden="true" />
                                            </button>
                                        ))
                                    ) : (
                                        <p className="col-span-full py-3 text-center text-sm font-medium text-pink-800">
                                            {commandSearch ? `No command matches “${commandSearch}”.` : 'Every command is already allowed.'}
                                        </p>
                                    )}
                                </div>
                                {filteredCommands.length > 12 && (
                                    <p className="mt-2 text-xs font-medium text-pink-800">
                                        Showing 12 of {filteredCommands.length}. Type to narrow the list.
                                    </p>
                                )}
                            </div>
                        )}

                        <div className="flex items-center justify-between gap-3 border-t-4 border-pink-950 bg-pink-100 px-6 py-4">
                            <p className="text-xs font-medium text-pink-900">
                                {selectedChannel.cmd_mode === 'all' ? '' : 'Save from the bar at the bottom of the page.'}
                            </p>
                            <button className="pixel-button-light px-4 py-2 text-xs" onClick={closeDialog}>
                                Done
                            </button>
                        </div>
                    </div>
                )}
                <form method="dialog" className="modal-backdrop">
                    <button aria-label="Close">close</button>
                </form>
            </dialog>
        </>
    );
}
