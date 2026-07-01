'use client';

import { useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

function CallbackHandler() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { setAuth } = useAuth();

    const hasRunRef = useRef(false);

    useEffect(() => {
        if (hasRunRef.current) return;
        hasRunRef.current = true;

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
                const response = await fetch(
                    `/api/proxy/api/auth/callback?code=${encodeURIComponent(code)}`
                );

                const text = await response.text();

                if (!response.ok) {
                    throw new Error('Failed to authenticate');
                }

                const data = JSON.parse(text);

                setAuth(data.token, data.user);
                router.replace('/dashboard');
            } catch (err) {
                console.error('Auth error:', err);
                router.push('/?error=auth_failed');
            }
        };

        handleCallback();
    }, [searchParams, router, setAuth]);

    return (
        <div className="flex min-h-screen flex-col items-center justify-center pixel-page px-4 text-center">
            <div className="mb-6 h-16 w-16 animate-spin border-4 border-pink-950 border-t-pink-500 bg-white shadow-[6px_6px_0_#8a174d]"></div>
            <h2 className="text-xl font-black uppercase text-pink-950">
                Authenticating with Discord...
            </h2>
            <p className="mt-2 text-sm font-bold text-pink-800">
                Please wait while we verify your account
            </p>
        </div>
    );
}

export default function CallbackPage() {
    return (
        <Suspense
            fallback={
                <div className="flex min-h-screen items-center justify-center pixel-page">
                    <div className="h-16 w-16 animate-spin border-4 border-pink-950 border-t-pink-500 bg-white shadow-[6px_6px_0_#8a174d]"></div>
                </div>
            }
        >
            <CallbackHandler />
        </Suspense>
    );
}
