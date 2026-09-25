"use client";

import {
    useEffect,
    useState
} from "react";

import {
    uploadDocument,
    getDocuments,
    deleteDocument
} from "@/lib/api";


export default function DocumentsPage() {

    const [documents, setDocuments] =
        useState<any[]>([]);

    const [file, setFile] =
        useState<File | null>(null);

    const [loading, setLoading] =
        useState(false);

    const [message, setMessage] =
        useState("");

    const [error, setError] =
        useState("");


    async function loadDocuments() {

        try {

            const result =
                await getDocuments();

            setDocuments(
                result.documents
            );

        } catch (err: any) {

            setError(
                err.message
            );
        }
    }


    useEffect(() => {

        loadDocuments();

    }, []);


    async function handleUpload() {

        if (!file) {

            setError(
                "Please select a PDF file."
            );

            return;
        }


        setLoading(true);

        setMessage("");

        setError("");


        try {

            const result =
                await uploadDocument(
                    file
                );


            setMessage(

                `Uploaded successfully: ${
                    result.file_name
                }`
            );


            setFile(null);

            await loadDocuments();


        } catch (err: any) {

            setError(
                err.message
            );

        } finally {

            setLoading(false);
        }
    }


    async function handleDelete(
        documentId: string
    ) {

        const confirmed =
            window.confirm(
                "Delete this document?"
            );


        if (!confirmed) {
            return;
        }


        try {

            await deleteDocument(
                documentId
            );


            await loadDocuments();


        } catch (err: any) {

            setError(
                err.message
            );
        }
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
                Documents
            </h1>


            <p className="
                text-gray-500
                mb-8
            ">
                Upload enterprise knowledge documents
            </p>


            <div className="
                bg-white
                rounded-2xl
                p-6
                shadow-sm
                mb-8
            ">

                <h2 className="
                    text-xl
                    font-bold
                    mb-4
                ">
                    Upload PDF
                </h2>


                <div className="
                    flex
                    gap-4
                    flex-wrap
                ">

                    <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => {

                            const selectedFile =
                                e.target.files?.[0];

                            setFile(
                                selectedFile || null
                            );
                        }}
                        className="
                            border
                            rounded-lg
                            p-3
                        "
                    />


                    <button
                        onClick={handleUpload}
                        disabled={loading}
                        className="
                            bg-black
                            text-white
                            px-6
                            py-3
                            rounded-lg
                        "
                    >

                        {loading
                            ? "Processing..."
                            : "Upload PDF"}

                    </button>

                </div>


                {message && (

                    <p className="
                        text-green-600
                        mt-4
                    ">
                        {message}
                    </p>
                )}


                {error && (

                    <p className="
                        text-red-600
                        mt-4
                    ">
                        {error}
                    </p>
                )}

            </div>


            <div className="
                bg-white
                rounded-2xl
                p-6
                shadow-sm
            ">

                <h2 className="
                    text-xl
                    font-bold
                    mb-4
                ">
                    Your Documents
                </h2>


                {documents.length === 0 ? (

                    <p className="
                        text-gray-500
                    ">
                        No documents uploaded.
                    </p>

                ) : (

                    <div className="
                        space-y-4
                    ">

                        {documents.map(
                            (document) => (

                                <div
                                    key={
                                        document.id
                                    }
                                    className="
                                        border
                                        rounded-xl
                                        p-4
                                        flex
                                        justify-between
                                        items-center
                                    "
                                >

                                    <div>

                                        <p className="
                                            font-semibold
                                        ">
                                            {
                                                document.file_name
                                            }
                                        </p>

                                        <p className="
                                            text-sm
                                            text-gray-500
                                            mt-1
                                        ">
                                            {
                                                document.page_count
                                            }
                                            {" "}pages •{" "}
                                            {
                                                document.chunk_count
                                            }
                                            {" "}chunks
                                        </p>

                                    </div>


                                    <button
                                        onClick={() =>
                                            handleDelete(
                                                document.id
                                            )
                                        }
                                        className="
                                            text-red-600
                                            border
                                            border-red-200
                                            px-4
                                            py-2
                                            rounded-lg
                                        "
                                    >
                                        Delete
                                    </button>

                                </div>
                            )
                        )}

                    </div>
                )}

            </div>

        </div>
    );
}
