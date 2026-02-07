import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function proxyRequest(request: NextRequest, path: string[]) {
    const targetPath = '/' + path.join('/');
    const url = new URL(request.url);
    const queryString = url.search;
    const targetUrl = `${API_URL}${targetPath}${queryString}`;

    const headers: Record<string, string> = {};

    const contentType = request.headers.get('Content-Type');

    if (contentType) {
        headers['Content-Type'] = contentType;
    }

    const authHeader = request.headers.get('Authorization');

    if (authHeader) {
        headers['Authorization'] = authHeader;
    }

    const fetchOptions: RequestInit = {
        method: request.method,
        headers,
    };


    if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
        try {
            const body = await request.text();
            if (body) {
                fetchOptions.body = body;
            }
        } catch {

        }
    }

    try {
        const response = await fetch(targetUrl, fetchOptions);
        const data = await response.text();

        return new NextResponse(data, {
            status: response.status,
            headers: {
                'Content-Type': response.headers.get('Content-Type') || 'application/json',
            },
        });
    } catch (error) {
        console.error('Proxy error:', error);
        return NextResponse.json(
            { error: 'Failed to connect to API' },
            { status: 502 }
        );
    }
}

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, path);
}

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, path);
}

export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, path);
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    return proxyRequest(request, path);
}
