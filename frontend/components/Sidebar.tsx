"use client";

import Link from "next/link";

import LogoutButton from "./LogoutButton";


export default function Sidebar() {

    return (

        <aside className="
            w-64
            min-h-screen
            bg-gray-950
            text-white
            p-6
            flex
            flex-col
        ">

            <div className="mb-10">

                <h1 className="
                    text-xl
                    font-bold
                ">
                    Enterprise GPT
                </h1>

                <p className="
                    text-gray-400
                    text-sm
                    mt-1
                ">
                    AI Knowledge Assistant
                </p>

            </div>


            <nav className="
                space-y-2
                flex-1
            ">

                <Link
                    href="/dashboard"
                    className="
                        block
                        px-4
                        py-3
                        rounded-lg
                        hover:bg-gray-800
                    "
                >
                    Dashboard
                </Link>


                <Link
                    href="/chat"
                    className="
                        block
                        px-4
                        py-3
                        rounded-lg
                        hover:bg-gray-800
                    "
                >
                    AI Chat
                </Link>


                <Link
                    href="/documents"
                    className="
                        block
                        px-4
                        py-3
                        rounded-lg
                        hover:bg-gray-800
                    "
                >
                    Documents
                </Link>

            </nav>


            <LogoutButton />

        </aside>
    );
}
