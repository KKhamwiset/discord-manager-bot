'use client';
import { authApi } from '@/lib/api';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
    id: string;
    username: string;
    avatar: string | null;
    global_name?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthorizedUser: boolean;
    login: () => void;
    logout: () => void;
    setAuth: (token: string, user: User, isAuthorized: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthorizedUser, setIsAuthorizedUser] = useState(false);

    useEffect(() => {
        const initAuth = async () => {
            const storedToken = localStorage.getItem('auth_token');
            const storedUser = localStorage.getItem('auth_user');

            if (!storedToken || !storedUser) {
                setIsLoading(false);
                return;
            }

            try {
                await authApi.me(storedToken);
                setToken(storedToken);
                setUser(JSON.parse(storedUser));

                try {
                    const authData = await authApi.authorizedUser(storedToken);
                    setIsAuthorizedUser(authData.authorized);
                } catch (e) {
                    console.error('Failed to check permission:', e);
                    setIsAuthorizedUser(false);
                }
            } catch (error) {
                console.error('Session validation failed:', error);
                logout();
            } finally {
                setIsLoading(false);
            }
        };

        initAuth();
    }, []);

    const login = async () => {
        try {
            const data = await authApi.login();
            window.location.href = data.url;
        } catch (error) {
            console.error('Login error:', error);
        }
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        setToken(null);
        setUser(null);
        setIsAuthorizedUser(false);
    };

    const setAuth = (newToken: string, newUser: User, isAuthorized: boolean) => {
        localStorage.setItem('auth_token', newToken);
        localStorage.setItem('auth_user', JSON.stringify(newUser));
        setToken(newToken);
        setUser(newUser);
        setIsAuthorizedUser(isAuthorized);
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, isAuthorizedUser, login, logout, setAuth, }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
