import { createClient } from "./supabase/client";


// =====================================================
// API URL
// =====================================================

const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";


// =====================================================
// TYPES
// =====================================================

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
        data: { session },
    } =
        await supabase.auth.getSession();


    if (!session) {

        throw new Error(
            "You are not logged in."
        );
    }


    return {
        Authorization:
            `Bearer ${session.access_token}`,
    };
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


    const response = await fetch(
        `${API_URL}/upload`,
        {
            method: "POST",

            headers,

            body: formData,
        }
    );


    if (!response.ok) {

        const error = await response
            .json()
            .catch(() => null);


        throw new Error(
            error?.detail ||
            "Failed to upload document"
        );
    }


    return response.json();
}


// =====================================================
// NORMAL CHAT
// =====================================================

export async function sendQuestion(
    question: string
) {

    const authHeaders =
        await getAuthHeaders();


    const response = await fetch(
        `${API_URL}/chat`,
        {
            method: "POST",

            headers: {
                ...authHeaders,

                "Content-Type":
                    "application/json",
            },

            body: JSON.stringify({
                question: question,
            }),
        }
    );


    if (!response.ok) {

        const error = await response
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
// STREAMING CHAT
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

    // -------------------------------------------------
    // Get authentication token
    // -------------------------------------------------

    const authHeaders =
        await getAuthHeaders();


    // -------------------------------------------------
    // Send streaming request
    // -------------------------------------------------

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
                question: question,
            }),
        }
    );


    // -------------------------------------------------
    // Handle HTTP errors
    // -------------------------------------------------

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


    // -------------------------------------------------
    // Check streaming response
    // -------------------------------------------------

    if (!response.body) {

        throw new Error(
            "Streaming response is not available"
        );
    }


    // -------------------------------------------------
    // Create stream reader
    // -------------------------------------------------

    const reader =
        response.body.getReader();


    const decoder =
        new TextDecoder();


    let buffer = "";

    let fullAnswer = "";


    // -------------------------------------------------
    // Helper for processing one NDJSON event
    // -------------------------------------------------

    function processEvent(
        line: string
    ) {

        if (!line.trim()) {
            return;
        }


        const event =
            JSON.parse(line);


        // ---------------------------------------------
        // Answer chunk
        // ---------------------------------------------

        if (
            event.type ===
            "chunk"
        ) {

            const content =
                event.content || "";


            fullAnswer +=
                content;


            onChunk(
                content
            );


            return;
        }


        // ---------------------------------------------
        // Sources
        // ---------------------------------------------

        if (
            event.type ===
            "sources"
        ) {

            onSources(
                event.sources || []
            );


            return;
        }


        // ---------------------------------------------
        // Backend streaming error
        // ---------------------------------------------

        if (
            event.type ===
            "error"
        ) {

            throw new Error(
                event.message ||
                "Streaming failed"
            );
        }
    }


    // -------------------------------------------------
    // Read streaming response
    // -------------------------------------------------

    while (true) {

        const {
            done,
            value,
        } =
            await reader.read();


        if (done) {
            break;
        }


        // ---------------------------------------------
        // Convert bytes to text
        // ---------------------------------------------

        buffer +=
            decoder.decode(
                value,
                {
                    stream: true,
                }
            );


        // ---------------------------------------------
        // Split NDJSON using newline
        // ---------------------------------------------

        const lines =
            buffer.split("\n");


        // Last line may be incomplete.
        // Keep it for the next chunk.
        buffer =
            lines.pop() || "";


        // ---------------------------------------------
        // Process complete JSON lines
        // ---------------------------------------------

        for (
            const line of lines
        ) {

            try {

                processEvent(
                    line
                );

            }

            catch (error) {

                console.error(
                    "Stream parsing error:",
                    error
                );


                throw error;
            }
        }
    }


    // -------------------------------------------------
    // Flush decoder
    // -------------------------------------------------

    buffer +=
        decoder.decode();


    // -------------------------------------------------
    // Process remaining JSON
    // -------------------------------------------------

    if (
        buffer.trim()
    ) {

        try {

            processEvent(
                buffer
            );

        }

        catch (error) {

            console.error(
                "Final stream parsing error:",
                error
            );


            throw error;
        }
    }


    // -------------------------------------------------
    // Return complete answer
    //
    // This is used later when saving the assistant
    // response into Supabase chat history.
    // -------------------------------------------------

    return fullAnswer;
}


// =====================================================
// GET USER DOCUMENTS
// =====================================================

export async function getDocuments() {

    const headers =
        await getAuthHeaders();


    const response = await fetch(
        `${API_URL}/documents`,
        {
            method: "GET",

            headers,
        }
    );


    if (!response.ok) {

        const error = await response
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
// DELETE USER DOCUMENT
// =====================================================

export async function deleteDocument(
    documentId: string
) {

    const headers =
        await getAuthHeaders();


    const response = await fetch(
        `${API_URL}/documents/${documentId}`,
        {
            method: "DELETE",

            headers,
        }
    );


    if (!response.ok) {

        const error = await response
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
// GET DASHBOARD
// =====================================================

export async function getDashboard() {

    const headers =
        await getAuthHeaders();


    const response = await fetch(
        `${API_URL}/dashboard`,
        {
            method: "GET",

            headers,
        }
    );


    if (!response.ok) {

        const error = await response
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

            headers,
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
// ADMIN - DELETE ANY DOCUMENT
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

            headers,
        }
    );


    if (!response.ok) {

        const error = await response
            .json()
            .catch(() => null);


        throw new Error(
            error?.detail ||
            "Failed to delete document"
        );
    }


    return response.json();
}
