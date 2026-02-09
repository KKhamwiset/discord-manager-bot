'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useState } from 'react';

export default function Header() {
    const { user, isAuthorizedUser, logout } = useAuth();
    const pathname = usePathname();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const isActive = (path: string) => pathname === path;

    if (!user) return null;

    const avatarUrl = user.avatar
        ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
        : `https://cdn.discordapp.com/embed/avatars/${parseInt(user.id) % 5}.png`;

    return (
        <header className="glass sticky top-0 z-50 border-b border-gray-800">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo and Desktop Nav */}
                    <div className="flex items-center gap-8">
                        <Link href="/dashboard" className="text-xl font-bold gradient-text">Bot Dashboard</Link>
                        <nav className="hidden md:flex gap-6">
                            <Link
                                href="/dashboard"
                                className={`font-medium transition-colors ${isActive('/dashboard') ? 'text-white' : 'text-gray-400 hover:text-white'}`}
                            >
                                Overview
                            </Link>
                            <Link
                                href="/commands"
                                className={`font-medium transition-colors ${isActive('/commands') ? 'text-white' : 'text-gray-400 hover:text-white'}`}
                            >
                                Commands
                            </Link>
                            {isAuthorizedUser && (
                                <Link
                                    href="/channels"
                                    className={`font-medium transition-colors ${isActive('/channels') ? 'text-white' : 'text-gray-400 hover:text-white'}`}
                                >
                                    Channels
                                </Link>
                            )}
                        </nav>
                    </div>

                    {/* Desktop User Profile */}
                    <div className="hidden md:flex items-center gap-4">
                        <div className="flex items-center gap-3">
                            <img
                                src={avatarUrl}
                                alt={user.username}
                                className="w-8 h-8 rounded-full ring-2 ring-purple-500/50"
                            />
                            <span className="text-sm font-medium">{user.username}</span>
                        </div>
                        <button
                            onClick={logout}
                            className="px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                        >
                            Logout
                        </button>
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="md:hidden flex items-center gap-4">
                        <img
                            src={avatarUrl}
                            alt={user.username}
                            className="w-8 h-8 rounded-full ring-2 ring-purple-500/50"
                        />
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
                        >
                            {isMenuOpen ? (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            ) : (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Menu Dropdown */}
            {isMenuOpen && (
                <div className="md:hidden border-t border-gray-800 bg-[#0a0a0f]/95 backdrop-blur-xl">
                    <div className="px-4 pt-2 pb-4 space-y-1">
                        <Link
                            href="/dashboard"
                            className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/dashboard')
                                ? 'bg-purple-600/10 text-purple-400'
                                : 'text-gray-300 hover:text-white hover:bg-gray-800'
                                }`}
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Overview
                        </Link>
                        <Link
                            href="/commands"
                            className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/commands')
                                ? 'bg-purple-600/10 text-purple-400'
                                : 'text-gray-300 hover:text-white hover:bg-gray-800'
                                }`}
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Commands
                        </Link>
                        <Link
                            href="/channels"
                            className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/channels')
                                ? 'bg-purple-600/10 text-purple-400'
                                : 'text-gray-300 hover:text-white hover:bg-gray-800'
                                }`}
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Channels
                        </Link>

                        <div className="border-t border-gray-800 my-2 pt-2">
                            <div className="px-3 py-2 flex items-center gap-3">
                                <span className="text-gray-400 text-sm">Logged in as <span className="text-white font-medium">{user.username}</span></span>
                            </div>
                            <button
                                onClick={() => {
                                    setIsMenuOpen(false);
                                    logout();
                                }}
                                className="w-full text-left block px-3 py-2 rounded-md text-base font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </header>
    );
}
