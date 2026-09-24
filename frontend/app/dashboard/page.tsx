"use client";

import {
    useEffect,
    useState
} from "react";

import {
    getDashboard
} from "@/lib/api";


export default function DashboardPage() {

    const [data, setData] =
        useState<any>(null);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");


    useEffect(() => {

        async function loadDashboard() {

            try {

                const result =
                    await getDashboard();

                setData(result);

            } catch (err: any) {

                setError(
                    err.message
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


            <div className="
                grid
                md:grid-cols-3
                gap-6
            ">

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
                        {data?.total_documents || 0}
                    </p>

                </div>


                <div className="
                    bg-white
                    p-6
                    rounded-2xl
                    shadow-sm
                ">

                    <p className="
                        text-gray-500
                    ">
                        Knowledge Chunks
                    </p>

                    <p className="
                        text-4xl
                        font-bold
                        mt-2
                    ">
                        {data?.total_chunks || 0}
                    </p>

                </div>


                <div className="
                    bg-white
                    p-6
                    rounded-2xl
                    shadow-sm
                ">

                    <p className="
                        text-gray-500
                    ">
                        AI Status
                    </p>

                    <p className="
                        text-2xl
                        font-bold
                        mt-2
                    ">
                        Active
                    </p>

                </div>

            </div>


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


                {data?.documents?.length === 0 ? (

                    <p className="
                        text-gray-500
                    ">
                        No documents uploaded yet.
                    </p>

                ) : (

                    <div className="
                        space-y-3
                    ">

                        {data?.documents?.map(
                            (document: any) => (

                                <div
                                    key={document.id}
                                    className="
                                        border
                                        rounded-lg
                                        p-4
                                        flex
                                        justify-between
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

                                        <p className="
                                            text-sm
                                            text-gray-500
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


                                    <span className="
                                        text-sm
                                        text-green-600
                                    ">
                                        {
                                            document.status
                                        }
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
