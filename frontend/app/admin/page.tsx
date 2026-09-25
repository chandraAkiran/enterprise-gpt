"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../../lib/supabase/client";

export default function AdminPage() {
    const router = useRouter();

    // Admin information
    const [email, setEmail] = useState("");

    // Dashboard statistics
    const [totalDocuments, setTotalDocuments] = useState(0);
    const [totalSessions, setTotalSessions] = useState(0);
    const [totalMessages, setTotalMessages] = useState(0);

    // Loading state
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function checkAdminAndLoadStats() {
            const supabase = createClient();

            try {
                // -----------------------------------------
                // 1. Get currently logged-in user
                // -----------------------------------------
                const {
                    data: { user },
                } = await supabase.auth.getUser();

                // User is not logged in
                if (!user) {
                    router.push("/login");
                    return;
                }

                // -----------------------------------------
                // 2. Check user's role
                // -----------------------------------------
                const { data: profile, error: profileError } =
                    await supabase
                        .from("profiles")
                        .select("role")
                        .eq("id", user.id)
                        .single();

                // User is not an admin
                if (
                    profileError ||
                    !profile ||
                    profile.role !== "admin"
                ) {
                    router.push("/dashboard");
                    return;
                }

                // Save admin email
                setEmail(user.email ?? "");

                // -----------------------------------------
                // 3. Count documents
                // -----------------------------------------
                const { count: documentCount } = await supabase
                    .from("documents")
                    .select("*", {
                        count: "exact",
                        head: true,
                    });

                // -----------------------------------------
                // 4. Count chat sessions
                // -----------------------------------------
                const { count: sessionCount } = await supabase
                    .from("chat_sessions")
                    .select("*", {
                        count: "exact",
                        head: true,
                    });

                // -----------------------------------------
                // 5. Count chat messages
                // -----------------------------------------
                const { count: messageCount } = await supabase
                    .from("chat_messages")
                    .select("*", {
                        count: "exact",
                        head: true,
                    });

                // -----------------------------------------
                // 6. Update dashboard statistics
                // -----------------------------------------
                setTotalDocuments(documentCount ?? 0);
                setTotalSessions(sessionCount ?? 0);
                setTotalMessages(messageCount ?? 0);

            } catch (error) {
                console.error(
                    "Admin dashboard error:",
                    error
                );
            } finally {
                setLoading(false);
            }
        }

        checkAdminAndLoadStats();
    }, [router]);

    // -----------------------------------------
    // Loading screen
    // -----------------------------------------
    if (loading) {
        return (
            <div className="p-8">
                <p className="text-gray-500">
                    Loading Admin Panel...
                </p>
            </div>
        );
    }

    // -----------------------------------------
    // Admin Dashboard
    // -----------------------------------------
    return (
        <div className="p-8">

            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold">
                    Admin Panel
                </h1>

                <p className="mt-2 text-gray-500">
                    Enterprise GPT Administration
                </p>
            </div>

            {/* Admin Information */}
            <div className="mt-8 rounded-lg border p-6">
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

            {/* Statistics */}
            <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">

                {/* Documents */}
                <div className="rounded-lg border p-6">
                    <p className="text-sm text-gray-500">
                        Total Documents
                    </p>

                    <p className="mt-2 text-3xl font-bold">
                        {totalDocuments}
                    </p>
                </div>

                {/* Chat Sessions */}
                <div className="rounded-lg border p-6">
                    <p className="text-sm text-gray-500">
                        Chat Sessions
                    </p>

                    <p className="mt-2 text-3xl font-bold">
                        {totalSessions}
                    </p>
                </div>

                {/* Chat Messages */}
                <div className="rounded-lg border p-6">
                    <p className="text-sm text-gray-500">
                        Chat Messages
                    </p>

                    <p className="mt-2 text-3xl font-bold">
                        {totalMessages}
                    </p>
                </div>

            </div>
        </div>
    );
}
