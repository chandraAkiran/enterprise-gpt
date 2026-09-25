import { createClient } from "./supabase/client";


const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";


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
// CHAT
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
            await response.json();

        throw new Error(
            error.detail ||
            "Failed to get answer"
        );
    }


    return response.json();
}


// =====================================================
// UPLOAD
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
            await response.json();

        throw new Error(
            error.detail ||
            "Upload failed"
        );
    }


    return response.json();
}


// =====================================================
// DOCUMENTS
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

        throw new Error(
            "Failed to load documents"
        );
    }


    return response.json();
}


// =====================================================
// DELETE
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

        throw new Error(
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

        throw new Error(
            "Failed to load dashboard"
        );
    }


    return response.json();
}

export async function getAdminDocuments() {
    const headers = await getAuthHeaders();

    const response = await fetch(
        `${API_URL}/admin/documents`,
        {
            method: "GET",
            headers,
        }
    );

    if (!response.ok) {
        const error = await response.json().catch(() => null);

        throw new Error(
            error?.detail ||
            "Failed to load admin documents"
        );
    }

    return response.json();
}


export async function adminDeleteDocument(
    documentId: string
) {
    const headers = await getAuthHeaders();

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
