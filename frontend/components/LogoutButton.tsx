"use client";

import { useRouter } from "next/navigation";

import { createClient } from "@/lib/supabase/client";


export default function LogoutButton() {

    const router =
        useRouter();

    const supabase =
        createClient();


    async function logout() {

        await supabase.auth.signOut();

        router.push("/login");

        router.refresh();
    }


    return (

        <button
            onClick={logout}
            className="
                px-4
                py-2
                rounded-lg
                bg-gray-900
                text-white
            "
        >
            Logout
        </button>
    );
}
