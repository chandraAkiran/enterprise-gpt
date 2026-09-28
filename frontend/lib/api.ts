import { createClient } from "./supabase/client";


const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";


export interface Source {
    source: string;
    page: number;
}


// =====================================================
// AUTH HEADERS
// =====================================================

async function getAuthHeaders() {

    const supabase =
        createClient();

    const {
        data: {
            session
        }
    } =
        await supabase.auth.getSession();

    if (!session) {

        throw new Error(
            "You are not logged in."
        );
    }

    return {
        Authorization:
            `Bearer ${session.access_token}`
    };
}


// =====================================================
// NORMAL CHAT
// =====================================================

export async function sendQuestion(
    question: string
) {

    const headers =
        await getAuthHeaders();

    const response =
        await fetch(
            `${API_URL}/chat`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",

                    ...headers
                },

                body: JSON.stringify({
                    question
                })
            }
        );

    if (!response.ok) {

        const error =
            await response
                .json()
                .catch(() => null);

        throw new Error(
            error?.detail ||
            "Failed to get answer"
        );
    }

    return response.json();
}


// =====================================================
// UPLOAD DOCUMENT
// =====================================================

export async function uploadDocument(
    file: File
) {

    const headers =
        await getAuthHeaders();

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    const response =
        await fetch(
            `${API_URL}/upload`,
            {
                method: "POST",

                headers,

                body: formData
            }
        );

    if (!response.ok) {

        const error =
            await response
                .json()
                .catch(() => null);

        throw new Error(
            error?.detail ||
            "Upload failed"
        );
    }

    return response.json();
}


// =====================================================
// GET DOCUMENTS
// =====================================================

export async function getDocuments() {

    const headers =
        await getAuthHeaders();

    const response =
        await fetch(
            `${API_URL}/documents`,
            {
                headers
            }
        );

    if (!response.ok) {

        const error =
            await response
                .json()
                .catch(() => null);

        throw new Error(
            error?.detail ||
            "Failed to load documents"
        );
    }

    return response.json();
}


// =====================================================
// DELETE DOCUMENT
// =====================================================

export async function deleteDocument(
    documentId: string
) {

    const headers =
        await getAuthHeaders();

    const response =
        await fetch(
            `${API_URL}/documents/${documentId}`,
            {
                method: "DELETE",

                headers
            }
        );

    if (!response.ok) {

        const error =
            await response
                .json()
                .catch(() => null);

        throw new Error(
            error?.detail ||
            "Failed to delete document"
        );
    }

    return response.json();
}


// =====================================================
// DASHBOARD
// =====================================================

export async function getDashboard() {

    const headers =
        await getAuthHeaders();

    const response =
        await fetch(
            `${API_URL}/dashboard`,
            {
                headers
            }
        );

    if (!response.ok) {

        const error =
            await response
                .json()
                .catch(() => null);

        throw new Error(
            error?.detail ||
            "Failed to load dashboard"
        );
    }

    return response.json();
}


// =====================================================
// ADMIN - GET ALL DOCUMENTS
// =====================================================

export async function getAdminDocuments() {

    const headers =
        await getAuthHeaders();

    const response = await fetch(
        `${API_URL}/admin/documents`,
        {
            method: "GET",
            headers
        }
    );

    if (!response.ok) {

        const error = await response
            .json()
            .catch(() => null);

        throw new Error(
            error?.detail ||
            "Failed to load admin documents"
        );
    }

    return response.json();
}


// =====================================================
// ADMIN - DELETE DOCUMENT
// =====================================================

export async function adminDeleteDocument(
    documentId: string
) {

    const headers =
        await getAuthHeaders();

    const response = await fetch(
        `${API_URL}/admin/documents/${documentId}`,
        {
            method: "DELETE",
            headers
        }
    );

    if (!response.ok) {

        const error = await response
            .json()
            .catch(() => null);

        throw new Error(
            error?.detail ||
            "Failed to delete admin document"
        );
    }

    return response.json();
}


// =====================================================
// AGENT CHAT
// =====================================================

export async function agentChat(
    question: string
) {

    const authHeaders =
        await getAuthHeaders();

    const response = await fetch(
        `${API_URL}/agent/chat`,
        {
            method: "POST",

            headers: {
                ...authHeaders,

                "Content-Type":
                    "application/json",
            },

            body: JSON.stringify({
                question
            }),
        }
    );

    if (!response.ok) {

        const error = await response
            .json()
            .catch(() => null);

        console.error(
            "Agent API error:",
            error
        );

        let message =
            "Failed to generate agent response";

        if (
            typeof error?.detail ===
            "string"
        ) {

            message =
                error.detail;
        }

        else if (
            error?.detail
        ) {

            message =
                JSON.stringify(
                    error.detail
                );
        }

        throw new Error(
            message
        );
    }

    return response.json();
}


// =====================================================
// AGENT STREAMING CHAT
// =====================================================

export async function streamAgentChat(
    question: string,

    onChunk: (
        chunk: string
    ) => void,

    onSources: (
        sources: Source[]
    ) => void
) {

    const authHeaders =
        await getAuthHeaders();

    const response = await fetch(
        `${API_URL}/agent/chat/stream`,
        {
            method: "POST",

            headers: {
                ...authHeaders,

                "Content-Type":
                    "application/json",
            },

            body: JSON.stringify({
                question
            }),
        }
    );

    if (!response.ok) {

        const error = await response
            .json()
            .catch(() => null);

        console.error(
            "Agent streaming API error:",
            error
        );

        let message =
            "Failed to stream Agent response";

        if (
            typeof error?.detail ===
            "string"
        ) {

            message =
                error.detail;
        }

        else if (
            error?.detail
        ) {

            message =
                JSON.stringify(
                    error.detail
                );
        }

        throw new Error(
            message
        );
    }

    if (!response.body) {

        throw new Error(
            "Streaming response body is missing"
        );
    }

    const reader =
        response.body.getReader();

    const decoder =
        new TextDecoder();

    let buffer = "";

    let fullAnswer = "";

    while (true) {

        const {
            value,
            done
        } =
            await reader.read();

        if (done) {
            break;
        }

        buffer += decoder.decode(
            value,
            {
                stream: true
            }
        );

        const lines =
            buffer.split("\n");

        buffer =
            lines.pop() || "";

        for (const line of lines) {

            if (!line.trim()) {
                continue;
            }

            const event =
                JSON.parse(line);

            // -----------------------------------------
            // ANSWER CHUNK
            // -----------------------------------------

            if (
                event.type ===
                "chunk"
            ) {

                const chunk =
                    event.content || "";

                fullAnswer +=
                    chunk;

                onChunk(
                    chunk
                );
            }

            // -----------------------------------------
            // SOURCES
            // -----------------------------------------

            else if (
                event.type ===
                "sources"
            ) {

                onSources(
                    event.sources || []
                );
            }

            // -----------------------------------------
            // ERROR
            // -----------------------------------------

            else if (
                event.type ===
                "error"
            ) {

                throw new Error(
                    event.message ||
                    "Agent streaming failed"
                );
            }
        }
    }

    // Handle any final buffered line.
    if (buffer.trim()) {

        const event =
            JSON.parse(buffer);

        if (
            event.type ===
            "chunk"
        ) {

            const chunk =
                event.content || "";

            fullAnswer +=
                chunk;

            onChunk(
                chunk
            );
        }

        else if (
            event.type ===
            "sources"
        ) {

            onSources(
                event.sources || []
            );
        }

        else if (
            event.type ===
            "error"
        ) {

            throw new Error(
                event.message ||
                "Agent streaming failed"
            );
        }
    }

    return fullAnswer;
}


// =====================================================
// ORIGINAL RAG STREAMING CHAT
// =====================================================

export async function streamChat(
    question: string,

    onChunk: (
        chunk: string
    ) => void,

    onSources: (
        sources: Source[]
    ) => void
) {

    const authHeaders =
        await getAuthHeaders();

    const response = await fetch(
        `${API_URL}/chat/stream`,
        {
            method: "POST",

            headers: {
                ...authHeaders,

                "Content-Type":
                    "application/json",
            },

            body: JSON.stringify({
                question
            }),
        }
    );

    if (!response.ok) {

        const error = await response
            .json()
            .catch(() => null);

        console.error(
            "Streaming API error:",
            error
        );

        let message =
            "Failed to stream response";

        if (
            typeof error?.detail ===
            "string"
        ) {

            message =
                error.detail;
        }

        else if (
            error?.detail
        ) {

            message =
                JSON.stringify(
                    error.detail
                );
        }

        throw new Error(
            message
        );
    }

    if (!response.body) {

        throw new Error(
            "Streaming response body is missing"
        );
    }

    const reader =
        response.body.getReader();

    const decoder =
        new TextDecoder();

    let buffer = "";

    let fullAnswer = "";

    while (true) {

        const {
            value,
            done
        } =
            await reader.read();

        if (done) {
            break;
        }

        buffer += decoder.decode(
            value,
            {
                stream: true
            }
        );

        const lines =
            buffer.split("\n");

        buffer =
            lines.pop() || "";

        for (const line of lines) {

            if (!line.trim()) {
                continue;
            }

            const event =
                JSON.parse(line);

            if (
                event.type ===
                "chunk"
            ) {

                const chunk =
                    event.content || "";

                fullAnswer +=
                    chunk;

                onChunk(
                    chunk
                );
            }

            else if (
                event.type ===
                "sources"
            ) {

                onSources(
                    event.sources || []
                );
            }

            else if (
                event.type ===
                "error"
            ) {

                throw new Error(
                    event.message ||
                    "Streaming failed"
                );
            }
        }
    }

    // Process final buffered event if present.
    if (buffer.trim()) {

        const event =
            JSON.parse(buffer);

        if (
            event.type ===
            "chunk"
        ) {

            const chunk =
                event.content || "";

            fullAnswer +=
                chunk;

            onChunk(
                chunk
            );
        }

        else if (
            event.type ===
            "sources"
        ) {

            onSources(
                event.sources || []
            );
        }

        else if (
            event.type ===
            "error"
        ) {

            throw new Error(
                event.message ||
                "Streaming failed"
            );
        }
    }

    return fullAnswer;
}
