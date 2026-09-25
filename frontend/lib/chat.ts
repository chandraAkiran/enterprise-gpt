import { createClient } from "./supabase/client";


// =====================================================
// CREATE CHAT SESSION
// =====================================================

export async function createChatSession(
    title: string
) {
    const supabase = createClient();

    const {
        data: { user }
    } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("You are not logged in.");
    }

    const {
        data,
        error
    } = await supabase
        .from("chat_sessions")
        .insert({
            user_id: user.id,
            title: title
        })
        .select()
        .single();

    if (error) {
        throw new Error(error.message);
    }

    return data;
}


// =====================================================
// SAVE CHAT MESSAGE
// =====================================================

export async function saveChatMessage(
    sessionId: string,
    role: "user" | "assistant",
    content: string
) {
    const supabase = createClient();

    const {
        data: { user }
    } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("You are not logged in.");
    }

    const {
        data,
        error
    } = await supabase
        .from("chat_messages")
        .insert({
            session_id: sessionId,
            user_id: user.id,
            role: role,
            content: content
        })
        .select()
        .single();

    if (error) {
        throw new Error(error.message);
    }

    return data;
}


// =====================================================
// GET CHAT SESSIONS
// =====================================================

export async function getChatSessions() {
    const supabase = createClient();

    const {
        data: { user }
    } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("You are not logged in.");
    }

    const {
        data,
        error
    } = await supabase
        .from("chat_sessions")
        .select("*")
        .eq("user_id", user.id)
        .order(
            "created_at",
            { ascending: false }
        );

    if (error) {
        throw new Error(error.message);
    }

    return data;
}


// =====================================================
// GET MESSAGES FOR ONE CHAT
// =====================================================

export async function getChatMessages(
    sessionId: string
) {
    const supabase = createClient();

    const {
        data: { user }
    } = await supabase.auth.getUser();

    if (!user) {
        throw new Error("You are not logged in.");
    }

    const {
        data,
        error
    } = await supabase
        .from("chat_messages")
        .select("*")
        .eq(
            "session_id",
            sessionId
        )
        .eq(
            "user_id",
            user.id
        )
        .order(
            "created_at",
            { ascending: true }
        );

    if (error) {
        throw new Error(error.message);
    }

    return data;
}
