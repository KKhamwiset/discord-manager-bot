'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import React, { ReactNode, useEffect, useState } from 'react';
import { authApi } from '@/lib/api';

export default function Header({ children }: { children?: ReactNode }) {
    const { user, logout } = useAuth();
    const pathname = usePathname();
    const [isAuthorizedUser, setIsAuthorizedUser] = useState(false);
    const [drawerOpen, setDrawerOpen] = useState(false);

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

    useEffect(() => {
        getAuthData();
    }, [user, logout]);

    if (!user) return null;

    const avatarUrl = user.avatar
        ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
        : `https://cdn.discordapp.com/embed/avatars/${parseInt(user.id) % 5}.png`;

    const isActive = (path: string) => pathname === path;

    const navItems = [
        { path: '/dashboard', label: 'Overview', icon: '🏠' },
        { path: '/commands', label: 'Commands', icon: '⚡' },
        ...(isAuthorizedUser ? [{ path: '/channels', label: 'Channels', icon: '📋' }] : []),
    ];

    return (
        <div className="drawer lg:drawer-open">
            <input id="sidebar-drawer" type="checkbox" className="drawer-toggle" checked={drawerOpen} onChange={() => setDrawerOpen(!drawerOpen)} />

            {/* Sidebar */}
            <div className="drawer-side z-50">
                <label htmlFor="sidebar-drawer" className="drawer-overlay"></label>
                <div className="menu bg-base-200 text-base-content min-h-full w-72 p-4 gap-2">
                    {/* Logo */}
                    <div className="mb-6 px-2">
                        <h1 className="text-2xl font-bold text-primary flex items-center gap-2">
                            🌸 Mochi Bot
                        </h1>
                        <p className="text-xs text-base-content/60 mt-1">Discord Dashboard</p>
                    </div>

                    {/* Nav Items */}
                    {navItems.map(item => (
                        <li key={item.path}>
                            <Link
                                href={item.path}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium transition-all ${
                                    isActive(item.path)
                                        ? 'bg-primary text-primary-content shadow-lg shadow-primary/20'
                                        : 'hover:bg-base-300 text-base-content/80'
                                }`}
                            >
                                <span className="text-lg">{item.icon}</span>
                                {item.label}
                            </Link>
                        </li>
                    ))}

                    <div className="divider my-2"></div>

                    {/* User Section */}
                    <div className="mt-auto">
                        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-base-300">
                            <div className="avatar">
                                <div className="w-10 rounded-full ring-2 ring-primary/30">
                                    <img src={avatarUrl} alt={user.username} />
                                </div>
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm truncate">{user.username}</p>
                                <p className="text-xs text-base-content/50">Logged in</p>
                            </div>
                        </div>
                        <li>
                            <button
                                onClick={logout}
                                className="flex items-center gap-3 px-4 py-3 rounded-xl text-error hover:bg-error/10 w-full text-left"
                            >
                                <span className="text-lg">🚪</span>
                                Logout
                            </button>
                        </li>
                    </div>
                </div>
            </div>

            {/* Main Content Wrapper */}
            <div className="drawer-content flex flex-col min-h-screen">
                {/* Top Navbar */}
                <div className="navbar bg-base-100 border-b border-base-200 px-4 sticky top-0 z-40">
                    <div className="flex-none lg:hidden">
                        <label htmlFor="sidebar-drawer" className="btn btn-ghost btn-square">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                        </label>
                    </div>
                    <div className="flex-1">
                        <h2 className="text-lg font-bold text-base-content">
                            {navItems.find(i => i.path === pathname)?.label || 'Dashboard'}
                        </h2>
                    </div>
                    <div className="flex-none">
                        <div className="dropdown dropdown-end">
                            <div tabIndex={0} role="button" className="btn btn-ghost btn-circle avatar">
                                <div className="w-10 rounded-full">
                                    <img src={avatarUrl} alt={user.username} />
                                </div>
                            </div>
                            <ul tabIndex={0} className="dropdown-content menu bg-base-200 rounded-box z-50 w-52 p-2 shadow-xl border border-base-300 mt-3">
                                <li className="menu-title"><span className="text-base-content/50">{user.username}</span></li>
                                <li><button onClick={logout} className="text-error">🚪 Logout</button></li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Page Content */}
                <main className="flex-1 p-4 md:p-6 lg:p-8">
                    {children}
                </main>
            </div>
        </div>
    );
}
