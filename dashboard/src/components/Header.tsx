'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useEffect, useState } from 'react';
import { authApi } from '@/lib/api';

export default function Header() {
    const { user, logout } = useAuth();
    const pathname = usePathname();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
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
    const isActive = (path: string) => pathname === path;
    useEffect(() => {
        getAuthData();
    },[user, logout]);
    
    if (!user) return null;

    const avatarUrl = user.avatar
        ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
        : `https://cdn.discordapp.com/embed/avatars/${parseInt(user.id) % 5}.png`;

    return (
        <header className="glass sticky top-0 z-50 border-b border-[#e8b4c8]">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    <div className="flex items-center gap-8">
                        <Link href="/dashboard" className="text-xl font-bold gradient-text">🌸 Mochi Dashboard</Link>
                        <nav className="hidden md:flex gap-6">
                            <Link href="/dashboard" className={`font-medium transition-colors ${isActive('/dashboard') ? 'text-[#d6197e]' : 'text-[#6b3a5a] hover:text-[#2d1028]'}`}>Overview</Link>
                            <Link href="/commands" className={`font-medium transition-colors ${isActive('/commands') ? 'text-[#d6197e]' : 'text-[#6b3a5a] hover:text-[#2d1028]'}`}>Commands</Link>
                            {isAuthorizedUser && (
                                <Link href="/channels" className={`font-medium transition-colors ${isActive('/channels') ? 'text-[#d6197e]' : 'text-[#6b3a5a] hover:text-[#2d1028]'}`}>Channels</Link>
                            )}
                        </nav>
                    </div>
                    <div className="hidden md:flex items-center gap-4">
                        <div className="flex items-center gap-3">
                            <img src={avatarUrl} alt={user.username} className="w-8 h-8 rounded-full ring-2 ring-pink-400/50" />
                            <span className="text-sm font-medium text-[#2d1028]">{user.username}</span>
                        </div>
                        <button onClick={logout} className="px-3 py-1.5 text-sm text-[#6b3a5a] hover:text-[#2d1028] hover:bg-[#ffe0ec] rounded-lg transition-colors">Logout</button>
                    </div>
                    <div className="md:hidden flex items-center gap-4">
                        <img src={avatarUrl} alt={user.username} className="w-8 h-8 rounded-full ring-2 ring-pink-400/50" />
                        <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="p-2 text-[#6b3a5a] hover:text-[#2d1028] rounded-lg hover:bg-[#ffe0ec] transition-colors">
                            {isMenuOpen ? (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                            ) : (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                            )}
                        </button>
                    </div>
                </div>
            </div>
            {isMenuOpen && (
                <div className="md:hidden border-t border-[#e8b4c8] bg-[#fff0f5]/95 backdrop-blur-xl">
                    <div className="px-4 pt-2 pb-4 space-y-1">
                        <Link href="/dashboard" className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/dashboard') ? 'bg-pink-100 text-pink-700' : 'text-[#6b3a5a] hover:text-[#2d1028] hover:bg-[#ffe0ec]'}`} onClick={() => setIsMenuOpen(false)}>Overview</Link>
                        <Link href="/commands" className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/commands') ? 'bg-pink-100 text-pink-700' : 'text-[#6b3a5a] hover:text-[#2d1028] hover:bg-[#ffe0ec]'}`} onClick={() => setIsMenuOpen(false)}>Commands</Link>
                        <Link href="/channels" className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/channels') ? 'bg-pink-100 text-pink-700' : 'text-[#6b3a5a] hover:text-[#2d1028] hover:bg-[#ffe0ec]'}`} onClick={() => setIsMenuOpen(false)}>Channels</Link>
                        <div className="border-t border-[#e8b4c8] my-2 pt-2">
                            <div className="px-3 py-2 flex items-center gap-3">
                                <span className="text-[#6b3a5a] text-sm">Logged in as <span className="text-[#2d1028] font-medium">{user.username}</span></span>
                            </div>
                            <button onClick={() => { setIsMenuOpen(false); logout(); }} className="w-full text-left block px-3 py-2 rounded-md text-base font-medium text-red-600 hover:text-red-700 hover:bg-red-50 transition-colors">Logout</button>
                        </div>
                    </div>
                </div>
            )}
        </header>
    );
}
