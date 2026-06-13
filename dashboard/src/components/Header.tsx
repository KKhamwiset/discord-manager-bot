'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useEffect, useState } from 'react';
import { authApi } from '@/lib/api';
import { ReactNode } from 'react';

export default function Header({ children }: { children?: ReactNode }) {
    const { user, logout } = useAuth();
    const pathname = usePathname();
    const [isAuthorizedUser, setIsAuthorizedUser] = useState(false);

    async function getAuthData() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            try {
                const authData = await authApi.authorizedUser(token);
                setIsAuthorizedUser(authData.authorized);
            } catch (error) {
                console.error('Failed to get authorized user data:', error);
            }
        }
        return null;
    }

    useEffect(() => { getAuthData(); }, [user, logout]);

    if (!user) return null;

    const avatarUrl = user.avatar
        ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
        : `https://cdn.discordapp.com/embed/avatars/${parseInt(user.id) % 5}.png`;

    const isActive = (path: string) => pathname === path;

    const navItems = [
        { path: '/dashboard', label: 'Overview' },
        { path: '/commands', label: 'Commands' },
        ...(isAuthorizedUser ? [{ path: '/channels', label: 'Channels' }] : []),
    ];

    return (
        <div className="flex flex-col min-h-screen">
            {/* Top Nav — Linear style */}
            <nav className="sticky top-0 z-50 bg-base-100/80 backdrop-blur-xl border-b border-base-300">
                <div className="max-w-6xl mx-auto px-4 sm:px-6">
                    <div className="flex items-center justify-between h-12">
                        {/* Left: Logo + Nav */}
                        <div className="flex items-center gap-6">
                            <Link href="/dashboard" className="flex items-center gap-2">
                                <span className="text-lg"></span>
                                <span className="font-semibold text-sm text-base-content">Mochi</span>
                            </Link>
                            <div className="hidden sm:flex items-center gap-1">
                                {navItems.map(item => (
                                    <Link
                                        key={item.path}
                                        href={item.path}
                                        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                                            isActive(item.path)
                                                ? 'bg-base-200 text-base-content'
                                                : 'text-base-content/60 hover:text-base-content hover:bg-base-200/50'
                                        }`}
                                    >
                                        {item.label}
                                    </Link>
                                ))}
                            </div>
                        </div>

                        {/* Right: User */}
                        <div className="flex items-center gap-3">
                            <div className="dropdown dropdown-end">
                                <div tabIndex={0} role="button" className="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-base-200 transition-colors cursor-pointer">
                                    <div className="avatar">
                                        <div className="w-7 h-7 rounded-full">
                                            <img src={avatarUrl} alt={user.username} />
                                        </div>
                                    </div>
                                    <span className="text-sm font-medium text-base-content/80 hidden sm:block">{user.username}</span>
                                    <svg className="w-3.5 h-3.5 text-base-content/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                                <ul tabIndex={0} className="dropdown-content menu bg-base-100 rounded-lg z-50 w-48 p-1 shadow-xl border border-base-300 mt-2">
                                    <li className="px-3 py-2 text-xs text-base-content/40 font-medium uppercase tracking-wider">{user.username}</li>
                                    <li><button onClick={logout} className="text-sm text-error hover:bg-error/5 rounded-md">Sign out</button></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Page Content */}
            <main className="flex-1">
                {children}
            </main>
        </div>
    );
}
