'use client';

import { authApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useEffect, useState } from 'react';

function avatarUrlFor(user: { id: string; avatar: string | null }) {
    if (user.avatar) {
        return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`;
    }
    // Discord's default avatar index for accounts without a custom one.
    const index = Number((BigInt(user.id) >> BigInt(22)) % BigInt(6));
    return `https://cdn.discordapp.com/embed/avatars/${index}.png`;
}

export default function Header({ children }: { children?: ReactNode }) {
    const { user, logout } = useAuth();
    const pathname = usePathname();
    const [isAuthorizedUser, setIsAuthorizedUser] = useState(false);

    useEffect(() => {
        let ignore = false;

        async function loadAuthData() {
            const token = localStorage.getItem('auth_token');
            if (!token) return;

            try {
                const authData = await authApi.authorizedUser(token);
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

    if (!user) return null;

    const displayName = user.global_name || user.username;

    const navItems = [
        { path: '/dashboard', label: 'Overview' },
        { path: '/commands', label: 'Commands' },
        ...(isAuthorizedUser ? [{ path: '/channels', label: 'Channels' }] : []),
    ];

    const navLinkClass = (path: string) => (
        pathname === path
            ? 'border-pink-950 bg-pink-600 text-white shadow-[3px_3px_0_#4a102c]'
            : 'border-pink-950 bg-white text-pink-950 hover:bg-pink-100 hover:shadow-[3px_3px_0_#4a102c]'
    );

    return (
        <div className="min-h-screen pixel-page text-pink-950">
            <nav aria-label="Main" className="sticky top-0 z-50 border-b-4 border-pink-950 bg-pink-200/95 font-mono">
                <div className="mx-auto max-w-6xl px-4 sm:px-6">
                    <div className="flex min-h-16 flex-wrap items-center justify-between gap-x-4 gap-y-3 py-3">
                        <Link href="/dashboard" className="flex items-center gap-3">
                            <span className="grid h-9 w-9 place-items-center border-4 border-pink-950 bg-pink-500 text-lg font-black text-white shadow-[3px_3px_0_#4a102c]">
                                M
                            </span>
                            <span className="text-sm font-black uppercase tracking-wide text-pink-950">
                                Mochi
                            </span>
                        </Link>

                        <div className="order-last flex w-full flex-wrap items-center gap-2 sm:order-none sm:w-auto">
                            {navItems.map((item) => (
                                <Link
                                    key={item.path}
                                    href={item.path}
                                    aria-current={pathname === item.path ? 'page' : undefined}
                                    className={`border-2 px-3 py-1.5 text-xs font-black uppercase hover:-translate-y-0.5 ${navLinkClass(item.path)}`}
                                >
                                    {item.label}
                                </Link>
                            ))}
                        </div>

                        <div className="dropdown dropdown-end">
                            <div
                                tabIndex={0}
                                role="button"
                                aria-label={`Account menu for ${displayName}`}
                                className="flex cursor-pointer items-center gap-2 border-2 border-pink-950 bg-white p-1 shadow-[3px_3px_0_#4a102c] hover:-translate-y-0.5 sm:pr-3"
                            >
                                <img
                                    src={avatarUrlFor(user)}
                                    alt=""
                                    width={32}
                                    height={32}
                                    className="h-8 w-8 border-2 border-pink-950"
                                />
                                <span className="hidden max-w-40 truncate text-xs font-black text-pink-950 sm:block">
                                    {displayName}
                                </span>
                            </div>
                            <ul tabIndex={0} className="dropdown-content menu z-50 mt-3 w-52 border-4 border-pink-950 bg-white p-1 shadow-[6px_6px_0_#4a102c]">
                                <li className="truncate px-3 py-2 text-xs font-bold text-pink-800">
                                    Signed in as {displayName}
                                </li>
                                <li>
                                    <button onClick={logout} className="text-sm font-bold text-pink-950 hover:bg-pink-100">
                                        Sign out
                                    </button>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="flex-1">
                {children}
            </main>
        </div>
    );
}
