/**
 * API Relay Handler for Next.js
 * 
 * This route acts as a proxy/relay between the frontend UI and the Python FastAPI backend.
 * It ensures that all frontend requests to /api/* are securely forwarded to the backend
 * while handling CORS and environment-specific routing.
 */

import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

/**
 * Handles incoming GET requests and proxies them to the internal backend.
 */
export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleProxy(request, params);
}

/**
 * Handles incoming POST requests and proxies them to the internal backend.
 */
export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleProxy(request, params);
}

/**
 * Handles incoming PUT requests and proxies them to the internal backend.
 */
export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleProxy(request, params);
}

/**
 * Handles incoming DELETE requests and proxies them to the internal backend.
 */
export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleProxy(request, params);
}

/**
 * Internal proxy logic that forwards requests to the FastAPI backend.
 * 
 * @param request - The incoming NextRequest object.
 * @param params - The dynamic path parameters.
 * @returns A NextResponse containing the backend's response.
 */
async function handleProxy(request: NextRequest, params: { path: string[] }) {
  const path = params.path.join('/');
  const query = request.nextUrl.search;
  
  // Use INTERNAL_API_URL if set (useful for Docker networking), otherwise fallback to localhost
  const backendUrl = process.env.INTERNAL_API_URL || 'http://localhost:8000';
  const targetUrl = `${backendUrl}/api/${path}${query}`;

  try {
    const headers = new Headers(request.headers);
    // Remove headers that might interfere with the proxy request
    headers.delete('host');
    headers.delete('connection');
    
    // Check if body should be sent (GET and HEAD requests should not have a body)
    const body = ['GET', 'HEAD'].includes(request.method) ? undefined : request.body;

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: headers,
      body: body as any, 
      // @ts-ignore: duplex option is required for streaming bodies in Node.js environments
      duplex: 'half' 
    });

    const newHeaders = new Headers(response.headers);
    // Remove encoding headers as the proxy will handle its own stream
    newHeaders.delete('content-encoding');
    newHeaders.delete('content-length');
    
    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders,
    });

  } catch (error) {
    console.error('Proxy Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
