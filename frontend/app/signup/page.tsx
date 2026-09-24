"use client";

import { useState } from "react";

import { useRouter } from "next/navigation";

import Link from "next/link";

import { createClient } from "@/lib/supabase/client";


export default function SignupPage() {

    const router =
        useRouter();

    const supabase =
        createClient();


    const [email, setEmail] =
        useState("");

    const [password, setPassword] =
        useState("");

    const [message, setMessage] =
        useState("");

    const [error, setError] =
        useState("");


    async function handleSignup(
        event: React.FormEvent
    ) {

        event.preventDefault();

        setMessage("");

        setError("");


        const {
            error
        } =
            await supabase.auth.signUp({

                email,

                password
            });


        if (error) {

            setError(
                error.message
            );

            return;
        }


        setMessage(
            "Account created. Please check your email if email confirmation is enabled."
        );


        setTimeout(() => {

            router.push(
                "/login"
            );

        }, 2000);
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
                    Create Account
                </h1>


                <p className="
                    text-gray-500
                    mb-8
                ">
                    Create your Enterprise GPT account
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


                {message && (

                    <div className="
                        bg-green-100
                        text-green-700
                        p-3
                        rounded-lg
                        mb-4
                    ">
                        {message}
                    </div>
                )}


                <form
                    onSubmit={handleSignup}
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
                            minLength={6}
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
                        className="
                            w-full
                            bg-black
                            text-white
                            py-3
                            rounded-lg
                            font-medium
                        "
                    >
                        Create Account
                    </button>

                </form>


                <p className="
                    text-center
                    mt-6
                    text-gray-600
                ">

                    Already have an account?

                    {" "}

                    <Link
                        href="/login"
                        className="font-semibold"
                    >
                        Login
                    </Link>

                </p>

            </div>

        </main>
    );
}
