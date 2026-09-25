"use client";

import {
    useEffect,
    useState
} from "react";

import {
    getDashboard,
    getDocuments
} from "@/lib/api";


interface DashboardData {
    documents: number;
    chat_sessions: number;
    chat_messages: number;
}


interface Document {
    id: string;
    file_name: string;
    file_path?: string;
    created_at?: string;
}


export default function DashboardPage() {

    const [data, setData] =
        useState<DashboardData | null>(null);

    const [documents, setDocuments] =
        useState<Document[]>([]);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");


    useEffect(() => {

        async function loadDashboard() {

            try {

                setError("");

                // Load dashboard counts
                const dashboardResult =
                    await getDashboard();

                setData(
                    dashboardResult
                );


                // Load actual document list
                const documentsResult =
                    await getDocuments();

                setDocuments(
                    documentsResult?.documents || []
                );

            } catch (err: unknown) {

                const message =
                    err instanceof Error
                        ? err.message
                        : "Failed to load dashboard";

                setError(
                    message
                );

            } finally {

                setLoading(false);
            }
        }


        loadDashboard();

    }, []);


    if (loading) {

        return (

            <div className="p-8">

                Loading dashboard...

            </div>
        );
    }


    return (

        <div className="
            p-8
            max-w-7xl
        ">

            <h1 className="
                text-3xl
                font-bold
                mb-2
            ">
                Dashboard
            </h1>


            <p className="
                text-gray-500
                mb-8
            ">
                Enterprise Knowledge Assistant
            </p>


            {error && (

                <div className="
                    bg-red-100
                    text-red-700
                    p-4
                    rounded-lg
                    mb-6
                ">
                    {error}
                </div>
            )}


            {/* ============================= */}
            {/* DASHBOARD CARDS */}
            {/* ============================= */}

            <div className="
                grid
                md:grid-cols-3
                gap-6
            ">

                {/* Documents */}

                <div className="
                    bg-white
                    p-6
                    rounded-2xl
                    shadow-sm
                ">

                    <p className="
                        text-gray-500
                    ">
                        Documents
                    </p>

                    <p className="
                        text-4xl
                        font-bold
                        mt-2
                    ">
                        {data?.documents ?? 0}
                    </p>

                </div>


                {/* Chat Sessions */}

                <div className="
                    bg-white
                    p-6
                    rounded-2xl
                    shadow-sm
                ">

                    <p className="
                        text-gray-500
                    ">
                        Chat Sessions
                    </p>

                    <p className="
                        text-4xl
                        font-bold
                        mt-2
                    ">
                        {data?.chat_sessions ?? 0}
                    </p>

                </div>


                {/* Chat Messages */}

                <div className="
                    bg-white
                    p-6
                    rounded-2xl
                    shadow-sm
                ">

                    <p className="
                        text-gray-500
                    ">
                        Chat Messages
                    </p>

                    <p className="
                        text-4xl
                        font-bold
                        mt-2
                    ">
                        {data?.chat_messages ?? 0}
                    </p>

                </div>

            </div>


            {/* ============================= */}
            {/* AI STATUS */}
            {/* ============================= */}

            <div className="
                bg-white
                rounded-2xl
                shadow-sm
                mt-8
                p-6
            ">

                <div className="
                    flex
                    items-center
                    justify-between
                ">

                    <div>

                        <h2 className="
                            text-xl
                            font-bold
                        ">
                            AI Knowledge Assistant
                        </h2>

                        <p className="
                            text-gray-500
                            mt-1
                        ">
                            Gemini RAG system
                        </p>

                    </div>


                    <span className="
                        text-green-600
                        font-medium
                    ">
                        ● Active
                    </span>

                </div>

            </div>


            {/* ============================= */}
            {/* RECENT DOCUMENTS */}
            {/* ============================= */}

            <div className="
                bg-white
                rounded-2xl
                shadow-sm
                mt-8
                p-6
            ">

                <h2 className="
                    text-xl
                    font-bold
                    mb-4
                ">
                    Recent Documents
                </h2>


                {documents.length === 0 ? (

                    <p className="
                        text-gray-500
                    ">
                        No documents uploaded yet.
                    </p>

                ) : (

                    <div className="
                        space-y-3
                    ">

                        {documents.map(
                            (document) => (

                                <div
                                    key={
                                        document.id
                                    }
                                    className="
                                        border
                                        rounded-lg
                                        p-4
                                        flex
                                        justify-between
                                        items-center
                                    "
                                >

                                    <div>

                                        <p className="
                                            font-medium
                                        ">
                                            {
                                                document.file_name
                                            }
                                        </p>


                                        {document.created_at && (

                                            <p className="
                                                text-sm
                                                text-gray-500
                                                mt-1
                                            ">

                                                Uploaded{" "}

                                                {
                                                    new Date(
                                                        document.created_at
                                                    ).toLocaleString()
                                                }

                                            </p>

                                        )}

                                    </div>


                                    <span className="
                                        text-sm
                                        text-green-600
                                    ">
                                        Ready
                                    </span>

                                </div>
                            )
                        )}

                    </div>
                )}

            </div>

        </div>
    );
}
