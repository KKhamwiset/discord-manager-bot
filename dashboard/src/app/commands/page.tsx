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
            } catch (error) {
                console.error('Failed to fetch commands:', error);
            } finally {
                setLoading(false);
            }
        };

        void fetchData();
    }, [token]);

    const handleToggle = async (commandName: string, currentStatus: boolean) => {
        if (!token || toggling) return;

        setToggling(commandName);
        try {
            await commandsApi.toggle(token, commandName, !currentStatus);
            setCommands((prev) => prev.map((cmd) => (
                cmd.name === commandName ? { ...cmd, enable: !currentStatus } : cmd
            )));
        } catch (error) {
            console.error('Failed to toggle command:', error);
        } finally {
            setToggling(null);
        }
    };

    if (isLoading || !user) {
        return (
            <div className="flex min-h-screen items-center justify-center pixel-page">
                <span className="loading loading-spinner loading-md text-primary"></span>
            </div>
        );
    }

    const categories = ['all', ...new Set(commands.map((command) => command.cog))];
    const filteredCommands = filter === 'all'
        ? commands
        : commands.filter((command) => command.cog === filter);

    return (
        <Header>
            <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
                <div className="mb-6 pixel-panel p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                        <div>
                            <div className="mb-3 inline-flex items-center gap-2 border-2 border-pink-950 bg-white px-3 py-1.5 text-xs font-black uppercase shadow-[3px_3px_0_#8a174d]">
                                <CommandLineIcon className="h-4 w-4 text-pink-700" aria-hidden="true" />
                                Command Arcade
                            </div>
                            <h1 className="text-3xl font-black uppercase text-pink-950">Commands</h1>
                            <p className="mt-1 text-sm font-bold text-pink-800">
                                {commands.length} total command cartridges loaded.
                            </p>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            {categories.map((category) => (
                                <button
                                    key={category}
                                    onClick={() => setFilter(category)}
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

                <div className="pixel-panel overflow-hidden bg-white">
                    <div className="pixel-table-head grid grid-cols-12 gap-4 px-4 py-3">
                        <div className="col-span-4">Name</div>
                        <div className="col-span-2">Category</div>
                        <div className="col-span-4">Description</div>
                        <div className="col-span-2 text-right">Status</div>
                    </div>

                    {loading ? (
                        [...Array(6)].map((_, index) => (
                            <div key={index} className="pixel-row grid grid-cols-12 gap-4 px-4 py-4 animate-pulse">
                                <div className="col-span-4"><div className="h-4 w-3/4 bg-pink-200"></div></div>
                                <div className="col-span-2"><div className="h-4 w-1/2 bg-pink-200"></div></div>
                                <div className="col-span-4"><div className="h-4 w-full bg-pink-200"></div></div>
                                <div className="col-span-2"><div className="ml-auto h-4 w-1/2 bg-pink-200"></div></div>
                            </div>
                        ))
                    ) : filteredCommands.length > 0 ? (
                        filteredCommands.map((cmd) => (
                            <div key={cmd.name} className="pixel-row grid grid-cols-12 gap-4 px-4 py-4">
                                <div className="col-span-4 flex min-w-0 items-center gap-3">
                                    <div className="grid h-9 w-9 flex-shrink-0 place-items-center border-2 border-pink-950 bg-pink-200">
                                        <CommandLineIcon className="h-5 w-5 text-pink-800" aria-hidden="true" />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="truncate text-sm font-black text-pink-950">{cmd.name}</p>
                                        {cmd.aliases && cmd.aliases.length > 0 && (
                                            <p className="truncate text-xs font-bold text-pink-700">{cmd.aliases.join(', ')}</p>
                                        )}
                                    </div>
                                </div>
                                <div className="col-span-2 flex items-center">
                                    <span className="pixel-chip px-2 py-1">{cmd.cog}</span>
                                </div>
                                <div className="col-span-4 flex items-center">
                                    <p className="truncate text-sm font-bold text-pink-800">{cmd.description || 'No description'}</p>
                                </div>
                                <div className="col-span-2 flex items-center justify-end gap-2">
                                    {cmd.hidden && <span className="pixel-chip bg-red-100 px-2 py-1">Hidden</span>}
                                    {isAuthorizedUser ? (
                                        <button
                                            onClick={() => handleToggle(cmd.name, cmd.enable)}
                                            disabled={toggling === cmd.name}
                                            className={`border-2 border-pink-950 px-3 py-1 text-xs font-black uppercase ${
                                                cmd.enable ? 'bg-emerald-200 text-emerald-950' : 'bg-pink-100 text-pink-950'
                                            } disabled:opacity-60`}
                                        >
                                            {toggling === cmd.name ? '...' : cmd.enable ? 'On' : 'Off'}
                                        </button>
                                    ) : (
                                        <span className={`text-xs font-black uppercase ${cmd.enable ? 'text-emerald-700' : 'text-pink-400'}`}>
                                            {cmd.enable ? 'Enabled' : 'Disabled'}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="py-16 text-center">
                            <p className="font-black uppercase text-pink-700">No commands found</p>
                        </div>
                    )}
                </div>
            </div>
        </Header>
    );
}
