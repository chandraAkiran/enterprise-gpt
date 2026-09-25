"use client";

import { useEffect, useState } from "react";
import { streamChat, Source } from "@/lib/api";
import { createChatSession, saveChatMessage, getChatSessions, getChatMessages } from "@/lib/chat";

interface Message { role: "user" | "assistant"; content: string; sources?: Source[]; }
interface ChatSession { id: string; title: string; created_at?: string; }

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  async function loadSessions() {
    try { setSessions((await getChatSessions()) ?? []); }
    catch (error) { console.error("Failed to load chat sessions:", error); }
    finally { setHistoryLoading(false); }
  }

  useEffect(() => { loadSessions(); }, []);

  async function openSession(selectedSessionId: string) {
    if (loading) return;
    try {
      setHistoryLoading(true);
      const data = await getChatMessages(selectedSessionId);
      const loadedMessages: Message[] = (data ?? []).map((message: { role: "user" | "assistant"; content: string }) => ({ role: message.role, content: message.content }));
      setSessionId(selectedSessionId);
      setMessages(loadedMessages);
    } catch (error) { console.error("Failed to load messages:", error); }
    finally { setHistoryLoading(false); }
  }

  function startNewChat() {
    if (loading) return;
    setSessionId(null); setMessages([]); setQuestion("");
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!question.trim() || loading) return;
    const currentQuestion = question.trim();
    setMessages(previous => [...previous, { role: "user", content: currentQuestion }]);
    setQuestion(""); setLoading(true);
    try {
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        const newSession = await createChatSession(currentQuestion.slice(0, 60));
        currentSessionId = newSession.id;
        setSessionId(currentSessionId);
        setSessions(previous => [newSession, ...previous]);
      }
      await saveChatMessage(currentSessionId!, "user", currentQuestion);
      setMessages(previous => [...previous, { role: "assistant", content: "", sources: [] }]);
      const fullAnswer = await streamChat(
        currentQuestion,
        (chunk: string) => setMessages(previous => {
          const updated = [...previous]; const i = updated.length - 1; const last = updated[i];
          if (last?.role === "assistant") updated[i] = { ...last, content: last.content + chunk };
          return updated;
        }),
        (sources: Source[]) => setMessages(previous => {
          const updated = [...previous]; const i = updated.length - 1; const last = updated[i];
          if (last?.role === "assistant") updated[i] = { ...last, sources };
          return updated;
        })
      );
      await saveChatMessage(currentSessionId!, "assistant", fullAnswer);
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Something went wrong";
      setMessages(previous => {
        const updated = [...previous]; const i = updated.length - 1; const last = updated[i];
        if (last?.role === "assistant") { updated[i] = { ...last, content: last.content ? `${last.content}\n\nError: ${errorMessage}` : `Error: ${errorMessage}` }; return updated; }
        return [...updated, { role: "assistant", content: `Error: ${errorMessage}` }];
      });
    } finally { setLoading(false); }
  }

  return (
    <div className="h-screen flex bg-gray-50">
      <aside className="w-72 border-r bg-white flex flex-col">
        <div className="p-4 border-b"><button type="button" onClick={startNewChat} disabled={loading} className="w-full bg-black text-white rounded-xl px-4 py-3 font-medium disabled:opacity-50">+ New Chat</button></div>
        <div className="px-4 pt-4 pb-2 text-sm font-semibold text-gray-500">Chat History</div>
        <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1">
          {historyLoading && sessions.length === 0 && <p className="px-3 py-2 text-sm text-gray-400">Loading...</p>}
          {!historyLoading && sessions.length === 0 && <p className="px-3 py-2 text-sm text-gray-400">No previous chats</p>}
          {sessions.map(session => <button key={session.id} type="button" onClick={() => openSession(session.id)} disabled={loading} className={`w-full text-left rounded-lg px-3 py-3 text-sm truncate ${sessionId === session.id ? "bg-gray-200 font-medium" : "hover:bg-gray-100"} disabled:opacity-50`} title={session.title}>{session.title || "Untitled chat"}</button>)}
        </div>
      </aside>
      <div className="flex-1 min-w-0 flex flex-col">
        <div className="p-8 border-b bg-white"><h1 className="text-3xl font-bold">AI Knowledge Assistant</h1><p className="text-gray-500 mt-1">Ask questions about your uploaded documents</p></div>
        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {messages.length === 0 && <div className="max-w-2xl mx-auto text-center mt-20"><h2 className="text-2xl font-bold mb-3">How can I help?</h2><p className="text-gray-500">Upload your enterprise documents and ask questions about them.</p></div>}
          {messages.map((message, index) => <div key={index} className={message.role === "user" ? "flex justify-end" : "flex justify-start"}><div className={message.role === "user" ? "max-w-2xl bg-black text-white rounded-2xl px-5 py-4" : "max-w-3xl bg-white border rounded-2xl px-5 py-4 shadow-sm"}>{message.role === "assistant" && message.content === "" && loading ? <p className="text-gray-500">Thinking...</p> : <p className="whitespace-pre-wrap">{message.content}</p>}{message.sources && message.sources.length > 0 && <div className="mt-4 pt-4 border-t"><p className="text-sm font-semibold mb-2">Sources</p><div className="space-y-1">{message.sources.map((source, sourceIndex) => <p key={sourceIndex} className="text-sm text-gray-500">{source.source}{" — "}Page {source.page}</p>)}</div></div>}</div></div>)}
        </div>
        <div className="border-t bg-white p-6"><form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-3"><input value={question} onChange={event => setQuestion(event.target.value)} disabled={loading} placeholder={loading ? "Generating answer..." : "Ask something about your documents..."} className="flex-1 border rounded-xl px-5 py-4 outline-none disabled:bg-gray-100"/><button type="submit" disabled={loading} className="bg-black text-white px-6 rounded-xl disabled:opacity-50">{loading ? "Generating..." : "Send"}</button></form></div>
      </div>
    </div>
  );
}
