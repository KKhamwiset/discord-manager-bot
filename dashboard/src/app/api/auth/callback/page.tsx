'use client';

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

function CallbackHandler() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { setAuth } = useAuth();

    useEffect(() => {
        const handleCallback = async () => {
            const code = searchParams.get('code');
            const error = searchParams.get('error');

            if (error) {
                console.error('OAuth error:', error);
                router.push('/?error=oauth_failed');
                return;
            }

            if (!code) {
                router.push('/');
                return;
            }

            try {

                const response = await fetch(`/api/proxy/api/auth/callback?code=${code}`);

                if (!response.ok) {
                    throw new Error('Failed to authenticate');
                }

                const data = await response.json();

                // Store auth data
                setAuth(data.token, data.user);

                router.push('/dashboard');
            } catch (err) {
                console.error('Auth error:', err);
                router.push('/?error=auth_failed');
            }
        };

        handleCallback();
    }, [searchParams, router, setAuth]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mb-6"></div>
            <h2 className="text-xl font-semibold text-gray-300">Authenticating with Discord...</h2>
            <p className="text-gray-500 mt-2">Please wait while we verify your account</p>
        </div>
    );
}

export default function CallbackPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        }>
            <CallbackHandler />
        </Suspense>
    );
}
