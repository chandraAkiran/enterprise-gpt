"use client";

import { useState } from "react";

import { useRouter } from "next/navigation";

import Link from "next/link";

import { createClient } from "@/lib/supabase/client";


export default function LoginPage() {

    const router =
        useRouter();

    const supabase =
        createClient();


    const [email, setEmail] =
        useState("");

    const [password, setPassword] =
        useState("");

    const [error, setError] =
        useState("");

    const [loading, setLoading] =
        useState(false);


    async function handleLogin(
        event: React.FormEvent
    ) {

        event.preventDefault();

        setError("");

        setLoading(true);


        const {
            error
        } =
            await supabase.auth.signInWithPassword({

                email,

                password
            });


        if (error) {

            setError(
                error.message
            );

            setLoading(false);

            return;
        }


        router.push(
            "/dashboard"
        );

        router.refresh();
    }


    return (

        <main className="
            min-h-screen
            flex
            items-center
            justify-center
            bg-gray-100
            p-6
        ">

            <div className="
                w-full
                max-w-md
                bg-white
                rounded-2xl
                shadow-lg
                p-8
            ">

                <h1 className="
                    text-3xl
                    font-bold
                    mb-2
                ">
                    Enterprise GPT
                </h1>


                <p className="
                    text-gray-500
                    mb-8
                ">
                    Sign in to your account
                </p>


                {error && (

                    <div className="
                        bg-red-100
                        text-red-700
                        p-3
                        rounded-lg
                        mb-4
                    ">
                        {error}
                    </div>
                )}


                <form
                    onSubmit={handleLogin}
                    className="space-y-5"
                >

                    <div>

                        <label className="
                            block
                            mb-2
                            font-medium
                        ">
                            Email
                        </label>

                        <input
                            type="email"
                            value={email}
                            onChange={(e) =>
                                setEmail(
                                    e.target.value
                                )
                            }
                            required
                            className="
                                w-full
                                border
                                rounded-lg
                                px-4
                                py-3
                            "
                        />

                    </div>


                    <div>

                        <label className="
                            block
                            mb-2
                            font-medium
                        ">
                            Password
                        </label>

                        <input
                            type="password"
                            value={password}
                            onChange={(e) =>
                                setPassword(
                                    e.target.value
                                )
                            }
                            required
                            className="
                                w-full
                                border
                                rounded-lg
                                px-4
                                py-3
                            "
                        />

                    </div>


                    <button
                        type="submit"
                        disabled={loading}
                        className="
                            w-full
                            bg-black
                            text-white
                            py-3
                            rounded-lg
                            font-medium
                        "
                    >
                        {loading
                            ? "Signing in..."
                            : "Sign In"}
                    </button>

                </form>


                <p className="
                    text-center
                    mt-6
                    text-gray-600
                ">

                    Don't have an account?

                    {" "}

                    <Link
                        href="/signup"
                        className="
                            font-semibold
                            text-black
                        "
                    >
                        Sign Up
                    </Link>

                </p>

            </div>

        </main>
    );
}
