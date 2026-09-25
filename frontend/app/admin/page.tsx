"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { createClient } from "../../lib/supabase/client";

import {
    getAdminDocuments,
    adminDeleteDocument,
} from "../../lib/api";


interface AdminDocument {
    id: string;
    user_id: string;
    file_name: string;
    file_path?: string;
    status: string;
    page_count?: number;
    chunk_count?: number;
    created_at: string;
}


export default function AdminPage() {
    const router = useRouter();

    // =================================================
    // ADMIN INFORMATION
    // =================================================

    const [email, setEmail] = useState("");


    // =================================================
    // DASHBOARD STATISTICS
    // =================================================

    const [totalDocuments, setTotalDocuments] =
        useState(0);

    const [totalSessions, setTotalSessions] =
        useState(0);

    const [totalMessages, setTotalMessages] =
        useState(0);


    // =================================================
    // ADMIN DOCUMENTS
    // =================================================

    const [documents, setDocuments] =
        useState<AdminDocument[]>([]);


    // =================================================
    // LOADING / ERROR
    // =================================================

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");

    const [deletingId, setDeletingId] =
        useState<string | null>(null);


    // =================================================
    // LOAD ADMIN DASHBOARD
    // =================================================

    useEffect(() => {

        async function loadAdminDashboard() {

            const supabase = createClient();

            try {

                // -------------------------------------
                // 1. Get logged-in user
                // -------------------------------------

                const {
                    data: { user },
                } = await supabase.auth.getUser();


                if (!user) {
                    router.push("/login");
                    return;
                }


                // -------------------------------------
                // 2. Check admin role
                // -------------------------------------

                const {
                    data: profile,
                    error: profileError,
                } = await supabase
                    .from("profiles")
                    .select("role")
                    .eq("id", user.id)
                    .single();


                if (
                    profileError ||
                    !profile ||
                    profile.role !== "admin"
                ) {
                    router.push("/dashboard");
                    return;
                }


                // -------------------------------------
                // 3. Save admin email
                // -------------------------------------

                setEmail(
                    user.email ?? ""
                );


                // -------------------------------------
                // 4. Load all system documents
                //    through protected backend
                // -------------------------------------

                const adminDocumentData =
                    await getAdminDocuments();


                setDocuments(
                    adminDocumentData.documents ?? []
                );


                setTotalDocuments(
                    adminDocumentData.total ?? 0
                );


                // -------------------------------------
                // 5. Count chat sessions
                // -------------------------------------

                const {
                    count: sessionCount,
                } = await supabase
                    .from("chat_sessions")
                    .select(
                        "*",
                        {
                            count: "exact",
                            head: true,
                        }
                    );


                // -------------------------------------
                // 6. Count chat messages
                // -------------------------------------

                const {
                    count: messageCount,
                } = await supabase
                    .from("chat_messages")
                    .select(
                        "*",
                        {
                            count: "exact",
                            head: true,
                        }
                    );


                setTotalSessions(
                    sessionCount ?? 0
                );


                setTotalMessages(
                    messageCount ?? 0
                );

            } catch (error) {

                console.error(
                    "Admin dashboard error:",
                    error
                );


                if (error instanceof Error) {

                    setError(
                        error.message
                    );

                } else {

                    setError(
                        "Failed to load Admin Panel"
                    );

                }

            } finally {

                setLoading(false);

            }
        }


        loadAdminDashboard();

    }, [router]);


    // =================================================
    // ADMIN DELETE DOCUMENT
    // =================================================

    async function handleDeleteDocument(
        documentId: string,
        fileName: string
    ) {

        // ---------------------------------------------
        // Ask admin for confirmation
        // ---------------------------------------------

        const confirmed = window.confirm(
            `Are you sure you want to delete "${fileName}"?`
        );


        if (!confirmed) {
            return;
        }


        try {

            // -----------------------------------------
            // Show deleting state
            // -----------------------------------------

            setDeletingId(
                documentId
            );

            setError("");


            // -----------------------------------------
            // Call protected backend endpoint
            // -----------------------------------------

            await adminDeleteDocument(
                documentId
            );


            // -----------------------------------------
            // Remove document from table
            // -----------------------------------------

            setDocuments(
                (currentDocuments) =>
                    currentDocuments.filter(
                        (document) =>
                            document.id !== documentId
                    )
            );


            // -----------------------------------------
            // Update total document count
            // -----------------------------------------

            setTotalDocuments(
                (currentTotal) =>
                    Math.max(
                        0,
                        currentTotal - 1
                    )
            );

        } catch (error) {

            console.error(
                "Admin delete error:",
                error
            );


            if (error instanceof Error) {

                setError(
                    error.message
                );

            } else {

                setError(
                    "Failed to delete document"
                );

            }

        } finally {

            setDeletingId(null);

        }
    }


    // =================================================
    // LOADING SCREEN
    // =================================================

    if (loading) {

        return (

            <div className="p-8">

                <p className="text-gray-500">
                    Loading Admin Panel...
                </p>

            </div>

        );
    }


    // =================================================
    // ADMIN PAGE
    // =================================================

    return (

        <div className="p-8">


            {/* =========================================
                HEADER
            ========================================= */}

            <div>

                <h1 className="text-3xl font-bold">
                    Admin Panel
                </h1>

                <p className="mt-2 text-gray-500">
                    Enterprise GPT Administration
                </p>

            </div>


            {/* =========================================
                ERROR MESSAGE
            ========================================= */}

            {error && (

                <div
                    className="
                        mt-6
                        rounded-lg
                        border
                        border-red-200
                        bg-red-50
                        p-4
                        text-red-700
                    "
                >
                    {error}
                </div>

            )}


            {/* =========================================
                ADMIN INFORMATION
            ========================================= */}

            <div
                className="
                    mt-8
                    rounded-lg
                    border
                    p-6
                "
            >

                <p className="text-sm text-gray-500">
                    Logged in as
                </p>


                <p className="mt-1 font-semibold">
                    {email}
                </p>


                <p className="mt-2">

                    Role:{" "}

                    <span className="font-semibold">
                        Admin
                    </span>

                </p>

            </div>


            {/* =========================================
                STATISTICS
            ========================================= */}

            <div
                className="
                    mt-8
                    grid
                    grid-cols-1
                    gap-4
                    md:grid-cols-3
                "
            >


                {/* TOTAL DOCUMENTS */}

                <div
                    className="
                        rounded-lg
                        border
                        p-6
                    "
                >

                    <p className="text-sm text-gray-500">
                        Total Documents
                    </p>


                    <p className="mt-2 text-3xl font-bold">
                        {totalDocuments}
                    </p>

                </div>


                {/* CHAT SESSIONS */}

                <div
                    className="
                        rounded-lg
                        border
                        p-6
                    "
                >

                    <p className="text-sm text-gray-500">
                        Chat Sessions
                    </p>


                    <p className="mt-2 text-3xl font-bold">
                        {totalSessions}
                    </p>

                </div>


                {/* CHAT MESSAGES */}

                <div
                    className="
                        rounded-lg
                        border
                        p-6
                    "
                >

                    <p className="text-sm text-gray-500">
                        Chat Messages
                    </p>


                    <p className="mt-2 text-3xl font-bold">
                        {totalMessages}
                    </p>

                </div>

            </div>


            {/* =========================================
                DOCUMENT MANAGEMENT
            ========================================= */}

            <div className="mt-10">


                {/* SECTION TITLE */}

                <div className="mb-4">

                    <h2 className="text-2xl font-bold">
                        Document Management
                    </h2>


                    <p className="mt-1 text-sm text-gray-500">
                        Documents uploaded by Enterprise GPT users
                    </p>

                </div>


                {/* TABLE */}

                <div
                    className="
                        overflow-x-auto
                        rounded-lg
                        border
                    "
                >

                    <table className="w-full text-left">


                        {/* =================================
                            TABLE HEADER
                        ================================= */}

                        <thead className="bg-gray-50">

                            <tr>

                                <th
                                    className="
                                        p-4
                                        text-sm
                                        font-semibold
                                    "
                                >
                                    File
                                </th>


                                <th
                                    className="
                                        p-4
                                        text-sm
                                        font-semibold
                                    "
                                >
                                    User
                                </th>


                                <th
                                    className="
                                        p-4
                                        text-sm
                                        font-semibold
                                    "
                                >
                                    Status
                                </th>


                                <th
                                    className="
                                        p-4
                                        text-sm
                                        font-semibold
                                    "
                                >
                                    Pages
                                </th>


                                <th
                                    className="
                                        p-4
                                        text-sm
                                        font-semibold
                                    "
                                >
                                    Chunks
                                </th>


                                <th
                                    className="
                                        p-4
                                        text-sm
                                        font-semibold
                                    "
                                >
                                    Uploaded
                                </th>


                                <th
                                    className="
                                        p-4
                                        text-sm
                                        font-semibold
                                    "
                                >
                                    Action
                                </th>

                            </tr>

                        </thead>


                        {/* =================================
                            TABLE BODY
                        ================================= */}

                        <tbody>

                            {documents.map(
                                (document) => (

                                    <tr
                                        key={document.id}
                                        className="border-t"
                                    >


                                        {/* FILE NAME */}

                                        <td className="p-4">

                                            <p className="font-medium">
                                                {document.file_name}
                                            </p>

                                        </td>


                                        {/* USER ID */}

                                        <td className="p-4">

                                            <p
                                                className="
                                                    max-w-[180px]
                                                    truncate
                                                    text-sm
                                                "
                                                title={
                                                    document.user_id
                                                }
                                            >
                                                {document.user_id}
                                            </p>

                                        </td>


                                        {/* STATUS */}

                                        <td className="p-4">

                                            <span
                                                className="
                                                    rounded-full
                                                    border
                                                    px-3
                                                    py-1
                                                    text-xs
                                                    font-medium
                                                "
                                            >
                                                {document.status}
                                            </span>

                                        </td>


                                        {/* PAGE COUNT */}

                                        <td className="p-4">

                                            {
                                                document.page_count
                                                ?? 0
                                            }

                                        </td>


                                        {/* CHUNK COUNT */}

                                        <td className="p-4">

                                            {
                                                document.chunk_count
                                                ?? 0
                                            }

                                        </td>


                                        {/* UPLOAD DATE */}

                                        <td
                                            className="
                                                p-4
                                                text-sm
                                            "
                                        >

                                            {
                                                document.created_at

                                                    ? new Date(
                                                        document.created_at
                                                    ).toLocaleString()

                                                    : "-"
                                            }

                                        </td>


                                        {/* DELETE BUTTON */}

                                        <td className="p-4">

                                            <button

                                                onClick={() =>
                                                    handleDeleteDocument(
                                                        document.id,
                                                        document.file_name
                                                    )
                                                }

                                                disabled={
                                                    deletingId
                                                    === document.id
                                                }

                                                className="
                                                    rounded-lg
                                                    bg-red-600
                                                    px-4
                                                    py-2
                                                    text-sm
                                                    font-medium
                                                    text-white
                                                    hover:bg-red-700
                                                    disabled:cursor-not-allowed
                                                    disabled:opacity-50
                                                "
                                            >

                                                {
                                                    deletingId
                                                    === document.id

                                                        ? "Deleting..."

                                                        : "Delete"
                                                }

                                            </button>

                                        </td>

                                    </tr>

                                )
                            )}


                            {/* =================================
                                EMPTY STATE
                            ================================= */}

                            {documents.length === 0 && (

                                <tr>

                                    <td
                                        colSpan={7}
                                        className="
                                            p-8
                                            text-center
                                            text-gray-500
                                        "
                                    >
                                        No documents found.
                                    </td>

                                </tr>

                            )}

                        </tbody>

                    </table>

                </div>

            </div>

        </div>
    );
}
