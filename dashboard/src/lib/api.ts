const API_URL = process.env.NEXT_PUBLIC_API_URL;

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
    guild: Record<string, unknown>;
    total_commands: number;
    commands_24h: number;
    bot_status: string;
}

export interface CommandStat {
    command: string;
    usage_count: number;
    last_used: number | null;
}

export interface ActivityData {
    date: string;
    commands: number;
}

export const statsApi = {
    getOverview: (token: string) =>
        apiFetch<StatsOverview>('/api/stats/overview', { token }),

    getCommandStats: (token: string) =>
        apiFetch<{ commands: CommandStat[] }>('/api/stats/commands', { token }),

    getActivity: (token: string) =>
        apiFetch<{ activity: ActivityData[] }>('/api/stats/activity', { token }),
};

// Commands API
export interface Command {
    name: string;
    category: string;
    enabled: boolean;
    description: string;
    usage_count: number;
}

export interface CommandLog {
    command: string;
    user: string;
    channel: string;
    timestamp: number;
    success: boolean;
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

    getLogs: (token: string, limit = 50) =>
        apiFetch<{ logs: CommandLog[] }>(`/api/commands/logs?limit=${limit}`, { token }),
};
