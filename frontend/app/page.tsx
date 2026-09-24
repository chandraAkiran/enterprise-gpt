import Link from "next/link";


export default function Home() {

    return (

        <main className="
            min-h-screen
            flex
            items-center
            justify-center
            p-8
        ">

            <div className="
                max-w-4xl
                text-center
            ">

                <p className="
                    text-sm
                    uppercase
                    tracking-widest
                    text-gray-500
                    mb-4
                ">
                    Enterprise AI
                </p>


                <h1 className="
                    text-5xl
                    md:text-6xl
                    font-bold
                    mb-6
                ">
                    AI Knowledge Assistant
                </h1>


                <p className="
                    text-xl
                    text-gray-500
                    max-w-2xl
                    mx-auto
                    mb-10
                ">
                    Upload enterprise documents,
                    search your knowledge base,
                    and get AI-powered answers
                    grounded in your documents.
                </p>


                <div className="
                    flex
                    justify-center
                    gap-4
                ">

                    <Link
                        href="/login"
                        className="
                            bg-black
                            text-white
                            px-7
                            py-4
                            rounded-xl
                        "
                    >
                        Get Started
                    </Link>


                    <Link
                        href="/signup"
                        className="
                            border
                            px-7
                            py-4
                            rounded-xl
                        "
                    >
                        Create Account
                    </Link>

                </div>

            </div>

        </main>
    );
}
   
