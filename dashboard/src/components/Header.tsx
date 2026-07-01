'use client';

import { authApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useEffect, useState } from 'react';

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

    const avatarUrl = user.avatar
        ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
        : `https://cdn.discordapp.com/embed/avatars/${parseInt(user.id) % 5}.png`;

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
            <nav className="sticky top-0 z-50 border-b-4 border-pink-950 bg-pink-200/95 font-mono">
                <div className="mx-auto max-w-6xl px-4 sm:px-6">
                    <div className="flex min-h-16 flex-col gap-3 py-3 sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex items-center justify-between gap-4">
                            <Link href="/dashboard" className="flex items-center gap-3">
                                <span className="grid h-9 w-9 place-items-center border-4 border-pink-950 bg-pink-500 text-lg font-black text-white shadow-[3px_3px_0_#4a102c]">
                                    M
                                </span>
                                <span>
                                    <span className="block text-sm font-black uppercase tracking-wide text-pink-950">
                                        Mochi
                                    </span>
                                    <span className="block text-[10px] font-bold uppercase tracking-wide text-pink-800">
                                        Pixel Control
                                    </span>
                                </span>
                            </Link>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                            {navItems.map((item) => (
                                <Link
                                    key={item.path}
                                    href={item.path}
                                    className={`border-2 px-3 py-1.5 text-xs font-black uppercase transition-transform hover:-translate-y-0.5 ${navLinkClass(item.path)}`}
                                >
                                    {item.label}
                                </Link>
                            ))}
                        </div>

                        <div className="dropdown dropdown-end">
                            <div
                                tabIndex={0}
                                role="button"
                                className="flex cursor-pointer items-center gap-2 border-2 border-pink-950 bg-white px-2 py-1 shadow-[3px_3px_0_#4a102c] transition-transform hover:-translate-y-0.5"
                            >
                                <div className="avatar">
                                    <div className="h-8 w-8 border-2 border-pink-950">
                                        <img src={avatarUrl} alt={user.username} />
                                    </div>
                                </div>
                                <span className="hidden text-xs font-black uppercase text-pink-950 sm:block">
                                    {user.username}
                                </span>
                            </div>
                            <ul tabIndex={0} className="dropdown-content menu z-50 mt-3 w-48 border-4 border-pink-950 bg-white p-1 shadow-[6px_6px_0_#4a102c]">
                                <li className="px-3 py-2 text-[10px] font-black uppercase tracking-wide text-pink-700">
                                    {user.username}
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
