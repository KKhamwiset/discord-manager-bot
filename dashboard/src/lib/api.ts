const API_URL = '/api/proxy';

interface FetchOptions extends RequestInit {
    token?: string | null;
}

export async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { token, ...fetchOptions } = options;

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...fetchOptions,
        headers,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Request failed' }));
        throw new Error(error.error || 'Request failed');
    }

    return response.json();
}

// Stats API
export interface StatsOverview {
    guild: {
        id?: string;
        name?: string;
        icon?: string;
        members?: number;
        region?: string;
        [key: string]: any;
    };
    bot_status: string;
}
// Commands API
export interface Command {
    name: string;
    cog: string;
    description: string;
    aliases: string[];
    hidden: boolean;
    enable: boolean;
}

export interface User {
    id: string;
    username: string;
    avatar: string | null;
    global_name?: string;
}

export interface Channel {
    id: string;
    name: string;
    cmd_mode: string;
    allowed_commands: string[];
}
export const channelAPI = {
    getChannel: (token: string) => apiFetch<{ channels: Channel[] }>('/api/channels/', { token }),

    updateChannelCommand: (token: string, channelId: string, command: string, action: 'add' | 'remove') =>
        apiFetch<{ success: boolean; action: string; command: string }>(`/api/channels/${channelId}`, {
            method: 'PATCH',
            token,
            body: JSON.stringify({ action, command }),
        }),
};

export const statsApi = {
    getOverview: () =>
        apiFetch<StatsOverview>('/api/stats/overview'),
};

export const authApi = {
    me: (token: string) =>
        apiFetch<User & { user_id: string }>('/api/auth/me', { token }),

    authorizedUser: (token: string, userId: string) =>
        apiFetch<{ authorized: boolean }>('/api/auth/authorized-user', { token, body: JSON.stringify({ user_id: userId }) }),

    login: () =>
        apiFetch<{ url: string }>('/api/auth/login'),
};

export const commandsApi = {
    list: (token: string) =>
        apiFetch<{ commands: Command[] }>('/api/commands/', { token }),

    toggle: (token: string, commandName: string, enabled: boolean) =>
        apiFetch<{ command: string; enabled: boolean }>(`/api/commands/${commandName}`, {
            method: 'PATCH',
            token,
            body: JSON.stringify({ enabled }),
        }),
}
