"use client";

import {
    useState
} from "react";

import {
    sendQuestion
} from "@/lib/api";


interface Message {

    role: "user" | "assistant";

    content: string;

    sources?: {
        source: string;
        page: number;
    }[];
}


export default function ChatPage() {

    const [question, setQuestion] =
        useState("");

    const [messages, setMessages] =
        useState<Message[]>([]);

    const [loading, setLoading] =
        useState(false);


    async function handleSubmit(
        event: React.FormEvent
    ) {

        event.preventDefault();


        if (!question.trim()) {

            return;
        }


        const currentQuestion =
            question;


        setMessages(
            previous => [

                ...previous,

                {
                    role:
                        "user",

                    content:
                        currentQuestion
                }
            ]
        );


        setQuestion("");

        setLoading(true);


        try {

            const result =
                await sendQuestion(
                    currentQuestion
                );


            setMessages(
                previous => [

                    ...previous,

                    {
                        role:
                            "assistant",

                        content:
                            result.answer,

                        sources:
                            result.sources
                    }
                ]
            );


        } catch (error: any) {

            setMessages(
                previous => [

                    ...previous,

                    {
                        role:
                            "assistant",

                        content:
                            `Error: ${
                                error.message
                            }`
                    }
                ]
            );


        } finally {

            setLoading(false);
        }
    }


    return (

        <div className="
            h-screen
            flex
            flex-col
        ">

            <div className="
                p-8
                border-b
                bg-white
            ">

                <h1 className="
                    text-3xl
                    font-bold
                ">
                    AI Knowledge Assistant
                </h1>

                <p className="
                    text-gray-500
                    mt-1
                ">
                    Ask questions about your uploaded documents
                </p>

            </div>


            <div className="
                flex-1
                overflow-y-auto
                p-8
                space-y-6
            ">

                {messages.length === 0 && (

                    <div className="
                        max-w-2xl
                        mx-auto
                        text-center
                        mt-20
                    ">

                        <h2 className="
                            text-2xl
                            font-bold
                            mb-3
                        ">
                            How can I help?
                        </h2>

                        <p className="
                            text-gray-500
                        ">
                            Upload your enterprise
                            documents and ask questions
                            about them.
                        </p>

                    </div>
                )}


                {messages.map(
                    (message, index) => (

                        <div
                            key={index}
                            className={
                                message.role ===
                                "user"

                                ? "flex justify-end"

                                : "flex justify-start"
                            }
                        >

                            <div
                                className={
                                    message.role ===
                                    "user"

                                    ? `
                                      max-w-2xl
                                      bg-black
                                      text-white
                                      rounded-2xl
                                      px-5
                                      py-4
                                      `

                                    : `
                                      max-w-3xl
                                      bg-white
                                      border
                                      rounded-2xl
                                      px-5
                                      py-4
                                      shadow-sm
                                      `
                                }
                            >

                                <p className="
                                    whitespace-pre-wrap
                                ">
                                    {
                                        message.content
                                    }
                                </p>


                                {message.sources &&
                                 message.sources.length > 0 && (

                                    <div className="
                                        mt-4
                                        pt-4
                                        border-t
                                    ">

                                        <p className="
                                            text-sm
                                            font-semibold
                                            mb-2
                                        ">
                                            Sources
                                        </p>


                                        <div className="
                                            space-y-1
                                        ">

                                            {message.sources.map(
                                                (
                                                    source,
                                                    sourceIndex
                                                ) => (

                                                    <p
                                                        key={
                                                            sourceIndex
                                                        }
                                                        className="
                                                            text-sm
                                                            text-gray-500
                                                        "
                                                    >
                                                        {source.source}
                                                        {" — "}
                                                        Page{" "}
                                                        {source.page}
                                                    </p>

                                                )
                                            )}

                                        </div>

                                    </div>
                                )}

                            </div>

                        </div>
                    )
                )}


                {loading && (

                    <div className="
                        flex
                        justify-start
                    ">

                        <div className="
                            bg-white
                            border
                            rounded-2xl
                            px-5
                            py-4
                        ">
                            Thinking...
                        </div>

                    </div>
                )}

            </div>


            <div className="
                border-t
                bg-white
                p-6
            ">

                <form
                    onSubmit={handleSubmit}
                    className="
                        max-w-4xl
                        mx-auto
                        flex
                        gap-3
                    "
                >

                    <input
                        value={question}
                        onChange={(e) =>
                            setQuestion(
                                e.target.value
                            )
                        }
                        placeholder="
                            Ask something about your documents...
                        "
                        className="
                            flex-1
                            border
                            rounded-xl
                            px-5
                            py-4
                            outline-none
                        "
                    />


                    <button
                        type="submit"
                        disabled={loading}
                        className="
                            bg-black
                            text-white
                            px-6
                            rounded-xl
                        "
                    >
                        Send
                    </button>

                </form>

            </div>

        </div>
    );
}
