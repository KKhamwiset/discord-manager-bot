'use client';

import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import { authApi, Command, commandsApi } from '@/lib/api';
import { CommandLineIcon } from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function CommandsPage() {
    const { user, token, isLoading } = useAuth();
    const router = useRouter();
    const [commands, setCommands] = useState<Command[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');
    const [toggling, setToggling] = useState<string | null>(null);
    const [isAuthorizedUser, setIsAuthorizedUser] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [loadFailed, setLoadFailed] = useState(false);

    useEffect(() => {
        let ignore = false;

        async function loadAuthData() {
            const authToken = localStorage.getItem('auth_token');
            if (!authToken) return;

            try {
                const authData = await authApi.authorizedUser(authToken);
                if (!ignore) {
                    setIsAuthorizedUser(authData.authorized);
                }
            } catch (error) {
                console.error('Failed to get authorized user data:', error);
            }
        }

        void loadAuthData();

        return () => {
            ignore = true;
        };
    }, [user]);

    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/');
        }
    }, [user, isLoading, router]);

    useEffect(() => {
        const fetchData = async () => {
            if (!token) return;

            try {
                const cmdData = await commandsApi.list(token);
                setCommands(cmdData.commands || []);
                setLoadFailed(false);
            } catch (error) {
                console.error('Failed to fetch commands:', error);
                setLoadFailed(true);
            } finally {
                setLoading(false);
            }
        };

        void fetchData();
    }, [token]);

    const handleToggle = async (commandName: string, currentStatus: boolean) => {
        if (!token || toggling) return;

        setErrorMessage(null);
        setToggling(commandName);
        try {
            await commandsApi.toggle(token, commandName, !currentStatus);
            setCommands((prev) => prev.map((cmd) => (
                cmd.name === commandName ? { ...cmd, enable: !currentStatus } : cmd
            )));
        } catch (error: unknown) {
            const err = error as Error;
            console.error('Failed to toggle command:', err);
            setErrorMessage(`Could not turn ${currentStatus ? 'off' : 'on'} ${commandName}: ${err.message || 'request failed'}. Try again.`);
        } finally {
            setToggling(null);
        }
    };

    if (isLoading || !user) {
        return (
            <div className="flex min-h-screen items-center justify-center pixel-page">
                <span className="loading loading-spinner loading-md text-primary" aria-label="Loading"></span>
            </div>
        );
    }

    const categories = ['all', ...new Set(commands.map((command) => command.cog))];
    const enabledCount = commands.filter((command) => command.enable).length;
    const filteredCommands = filter === 'all'
        ? commands
        : commands.filter((command) => command.cog === filter);

    return (
        <Header>
            <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
                <div className="mb-6 pixel-panel p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                        <div>
                            <h1 className="text-3xl font-black uppercase text-pink-950">Commands</h1>
                            <p className="mt-1 text-sm font-medium text-pink-900">
                                {loading
                                    ? 'Loading commands…'
                                    : isAuthorizedUser
                                        ? `${enabledCount} of ${commands.length} commands are on. Protected commands stay on.`
                                        : `${enabledCount} of ${commands.length} commands are on. Only server managers can change them.`}
                            </p>
                        </div>

                        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by category">
                            {categories.map((category) => (
                                <button
                                    key={category}
                                    onClick={() => setFilter(category)}
                                    aria-pressed={filter === category}
                                    className={`border-2 border-pink-950 px-3 py-1.5 text-xs font-black uppercase shadow-[3px_3px_0_#8a174d] ${
                                        filter === category
                                            ? 'bg-pink-600 text-white'
                                            : 'bg-white text-pink-950 hover:bg-pink-100'
                                    }`}
                                >
                                    {category}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {errorMessage && (
                    <div role="alert" className="mb-4 flex items-center justify-between gap-3 border-2 border-red-950 bg-red-100 p-3 text-sm font-bold text-red-900 shadow-[3px_3px_0_#8a174d]">
                        <span>{errorMessage}</span>
                        <button
                            onClick={() => setErrorMessage(null)}
                            className="flex-shrink-0 font-black uppercase underline underline-offset-2 hover:text-red-700"
                        >
                            Dismiss
                        </button>
                    </div>
                )}

                <div className="pixel-panel overflow-hidden bg-white">
                    <div className="pixel-table-head hidden grid-cols-12 gap-4 px-4 py-3 md:grid">
                        <div className="col-span-4">Name</div>
                        <div className="col-span-2">Category</div>
                        <div className="col-span-4">Description</div>
                        <div className="col-span-2 text-right">Status</div>
                    </div>

                    {loading ? (
                        [...Array(6)].map((_, index) => (
                            <div key={index} className="pixel-row grid grid-cols-[1fr_auto] gap-3 px-4 py-4 animate-pulse md:grid-cols-12 md:gap-4">
                                <div className="md:col-span-4"><div className="h-4 w-3/4 bg-pink-200"></div></div>
                                <div className="hidden md:col-span-2 md:block"><div className="h-4 w-1/2 bg-pink-200"></div></div>
                                <div className="hidden md:col-span-4 md:block"><div className="h-4 w-full bg-pink-200"></div></div>
                                <div className="md:col-span-2"><div className="ml-auto h-4 w-12 bg-pink-200"></div></div>
                            </div>
                        ))
                    ) : loadFailed ? (
                        <div className="px-6 py-16 text-center" role="alert">
                            <p className="font-black uppercase text-pink-950">Could not load commands</p>
                            <p className="mt-1 text-sm font-medium text-pink-900">The API did not answer. Refresh the page to try again.</p>
                        </div>
                    ) : filteredCommands.length > 0 ? (
                        filteredCommands.map((cmd) => (
                            <div key={cmd.name} className="pixel-row grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-2 px-4 py-4 md:grid-cols-12 md:gap-4">
                                <div className="flex min-w-0 items-center gap-3 md:col-span-4">
                                    <div className="grid h-9 w-9 flex-shrink-0 place-items-center border-2 border-pink-950 bg-pink-200">
                                        <CommandLineIcon className="h-5 w-5 text-pink-800" aria-hidden="true" />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="truncate text-sm font-black text-pink-950">{cmd.name}</p>
                                        {cmd.aliases && cmd.aliases.length > 0 && (
                                            <p className="truncate text-xs font-bold text-pink-800">
                                                <span className="sr-only">Aliases: </span>{cmd.aliases.join(', ')}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <div className="col-span-2 row-start-2 flex items-center md:row-start-auto">
                                    <span className="pixel-chip px-2 py-1">{cmd.cog}</span>
                                </div>
                                <div className="col-span-2 row-start-3 flex min-w-0 items-center md:col-span-4 md:row-start-auto">
                                    <p
                                        className={`text-sm font-medium md:truncate ${cmd.description ? 'text-pink-900' : 'italic text-pink-800'}`}
                                        title={cmd.description || undefined}
                                    >
                                        {cmd.description || 'No description'}
                                    </p>
                                </div>
                                <div className="col-start-2 row-start-1 flex flex-wrap items-center justify-end gap-2 md:col-span-2 md:col-start-auto md:row-start-auto">
                                    {cmd.hidden && <span className="pixel-chip bg-red-100 px-2 py-1">Hidden</span>}
                                    {cmd.protected ? (
                                        <span
                                            className="pixel-chip bg-amber-100 px-2 py-1"
                                            title="System command, always on"
                                        >
                                            Protected
                                        </span>
                                    ) : isAuthorizedUser ? (
                                        <button
                                            onClick={() => handleToggle(cmd.name, cmd.enable)}
                                            disabled={toggling !== null}
                                            aria-pressed={cmd.enable}
                                            aria-label={`${cmd.name}: ${cmd.enable ? 'on' : 'off'}`}
                                            className={`min-w-14 border-2 border-pink-950 px-3 py-1 text-xs font-black uppercase shadow-[2px_2px_0_#8a174d] hover:translate-x-px hover:translate-y-px hover:shadow-[1px_1px_0_#8a174d] ${
                                                cmd.enable ? 'bg-emerald-200 text-emerald-950' : 'bg-white text-pink-950'
                                            } disabled:cursor-wait disabled:opacity-60`}
                                        >
                                            {toggling === cmd.name ? '…' : cmd.enable ? 'On' : 'Off'}
                                        </button>
                                    ) : (
                                        <span className={`text-xs font-black uppercase ${cmd.enable ? 'text-emerald-800' : 'text-pink-800'}`}>
                                            {cmd.enable ? 'Enabled' : 'Disabled'}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="px-6 py-16 text-center">
                            <p className="font-black uppercase text-pink-950">
                                {commands.length === 0 ? 'No commands registered' : 'No commands in this category'}
                            </p>
                            {commands.length > 0 && (
                                <button onClick={() => setFilter('all')} className="mt-2 text-sm font-bold text-pink-800 underline underline-offset-2 hover:text-pink-950">
                                    Show all commands
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </Header>
    );
}
