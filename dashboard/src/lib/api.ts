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


export const statsApi = {
    getOverview: () =>
        apiFetch<StatsOverview>('/api/stats/overview'),
};

// Commands API
export interface Command {
    name: string;
    cog: string;
    description: string;
    aliases: string[];
    hidden: boolean
    enable: boolean
}



export const commandsApi = {
    list: (token: string) =>
        apiFetch<{ commands: Command[] }>('/api/commands', { token }),

    toggle: (token: string, commandName: string, enabled: boolean) =>
        apiFetch<{ command: string; enabled: boolean }>(`/api/commands/${commandName}`, {
            method: 'PATCH',
            token,
            body: JSON.stringify({ enabled }),
        }),
}
