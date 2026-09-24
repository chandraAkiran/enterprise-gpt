import type { Metadata } from "next";

import "./globals.css";

import Sidebar from "@/components/Sidebar";


export const metadata: Metadata = {

    title:
        "Enterprise GPT",

    description:
        "AI Knowledge Assistant"
};


export default function RootLayout({

    children

}: Readonly<{

    children: React.ReactNode

}>) {

    return (

        <html lang="en">

            <body>

                <div className="
                    flex
                    min-h-screen
                ">

                    <Sidebar />

                    <main className="
                        flex-1
                        bg-gray-100
                        min-h-screen
                    ">

                        {children}

                    </main>

                </div>

            </body>

        </html>
    );
}
