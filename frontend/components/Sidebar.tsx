"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import LogoutButton from "./LogoutButton";
import { createClient } from "../lib/supabase/client";

export default function Sidebar() {
    const [isAdmin, setIsAdmin] = useState(false);

    useEffect(() => {
        async function checkAdminRole() {
            const supabase = createClient();

            const {
                data: { user },
            } = await supabase.auth.getUser();

            if (!user) {
                setIsAdmin(false);
                return;
            }

            const { data: profile, error } = await supabase
                .from("profiles")
                .select("role")
                .eq("id", user.id)
                .single();

            if (!error && profile?.role === "admin") {
                setIsAdmin(true);
            } else {
                setIsAdmin(false);
            }
        }

        checkAdminRole();
    }, []);

    return (
        <aside
            className="
                w-64
                min-h-screen
                bg-gray-950
                text-white
                p-6
                flex
                flex-col
            "
        >
            {/* Title */}
            <div className="mb-10">
                <h1 className="text-xl font-bold">
                    Enterprise GPT
                </h1>

                <p className="text-gray-400 text-sm mt-1">
                    AI Knowledge Assistant
                </p>
            </div>

            {/* Navigation */}
            <nav className="space-y-2 flex-1">

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

                {/* Only admins can see this link */}
                {isAdmin && (
                    <Link
                        href="/admin"
                        className="
                            block
                            px-4
                            py-3
                            rounded-lg
                            hover:bg-gray-800
                        "
                    >
                        Admin Panel
                    </Link>
                )}

            </nav>

            <LogoutButton />
        </aside>
    );
}
