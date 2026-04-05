// src/App.jsx
import { useState, useRef, useEffect } from 'react'
import { sendMessage, getMemories, deleteMemory, deleteAllMemories } from './api'

// ── Icons (inline SVG to avoid extra deps) ──────────────────────────────────

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 2L11 13" /><path d="M22 2L15 22l-4-9-9-4 20-7z" />
  </svg>
)

const TrashIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6M14 11v6" /><path d="M9 6V4h6v2" />
  </svg>
)

const BrainIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
  </svg>
)

const SpinnerIcon = () => (
  <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
  </svg>
)

// ── Subcomponents ─────────────────────────────────────────────────────────────

function UserSetup({ onStart }) {
  const [userId, setUserId] = useState('')

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 mb-4 shadow-lg shadow-violet-500/25">
            <BrainIcon />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight" style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}>
            MemChat
          </h1>
          <p className="text-zinc-400 mt-2 text-sm">AI that actually remembers you</p>
        </div>

        {/* Card */}
        <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-8 backdrop-blur">
          <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-widest mb-3">
            Your User ID
          </label>
          <input
            type="text"
            value={userId}
            onChange={e => setUserId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && userId.trim() && onStart(userId.trim())}
            placeholder="e.g. rahul, demo_user, alice"
            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 text-sm focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-all"
            autoFocus
          />
          <p className="text-zinc-500 text-xs mt-2">
            Memories are scoped to this ID — use the same ID to continue a session.
          </p>
          <button
            onClick={() => userId.trim() && onStart(userId.trim())}
            disabled={!userId.trim()}
            className="w-full mt-5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all duration-200 text-sm tracking-wide"
          >
            Start Chatting →
          </button>
        </div>
      </div>
    </div>
  )
}

function ChatBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center mr-2 mt-0.5 flex-shrink-0">
          <BrainIcon />
        </div>
      )}
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-violet-600 text-white rounded-tr-sm'
            : 'bg-zinc-800 text-zinc-100 rounded-tl-sm border border-zinc-700'
        }`}
      >
        {msg.content}
      </div>
    </div>
  )
}

function MemoryPanel({ userId, memories, loading, onDelete, onDeleteAll, onRefresh }) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <BrainIcon />
          <span className="text-xs font-bold text-zinc-300 uppercase tracking-widest">Memory</span>
          {memories.length > 0 && (
            <span className="bg-violet-600/30 text-violet-300 text-xs px-2 py-0.5 rounded-full font-mono">
              {memories.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="text-zinc-500 hover:text-zinc-300 text-xs transition-colors"
            title="Refresh memories"
          >
            ↻
          </button>
          {memories.length > 0 && (
            <button
              onClick={onDeleteAll}
              className="text-zinc-500 hover:text-red-400 text-xs transition-colors"
              title="Forget everything"
            >
              Clear all
            </button>
          )}
        </div>
      </div>

      {/* Memory list */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center py-8 text-zinc-500">
            <SpinnerIcon />
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center py-10">
            <div className="text-3xl mb-2">🧠</div>
            <p className="text-zinc-500 text-xs">No memories yet.</p>
            <p className="text-zinc-600 text-xs mt-1">Start chatting — I'll remember what matters.</p>
          </div>
        ) : (
          memories.map((mem) => (
            <div
              key={mem.id}
              className="group flex items-start gap-2 bg-zinc-800/50 border border-zinc-700/50 rounded-xl px-3 py-2.5 hover:border-zinc-600 transition-all"
            >
              <span className="text-violet-400 text-xs mt-0.5 flex-shrink-0">◆</span>
              <p className="text-zinc-300 text-xs leading-relaxed flex-1">{mem.memory}</p>
              <button
                onClick={() => onDelete(mem.id)}
                className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition-all flex-shrink-0 mt-0.5"
                title="Delete this memory"
              >
                <TrashIcon />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-zinc-800">
        <p className="text-zinc-600 text-xs text-center">
          user: <span className="text-zinc-400 font-mono">{userId}</span>
        </p>
      </div>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [userId, setUserId] = useState(null)
  const [history, setHistory] = useState([])       // [{role, content}]
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [memories, setMemories] = useState([])
  const [memoriesLoading, setMemoriesLoading] = useState(false)
  const [showMemoryPanel, setShowMemoryPanel] = useState(true)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, loading])

  // Load memories whenever history updates (after bot replies)
  const refreshMemories = async (uid = userId) => {
    if (!uid) return
    setMemoriesLoading(true)
    try {
      const res = await getMemories(uid)
      setMemories(res.data.memories || [])
    } catch (e) {
      console.error('Failed to fetch memories', e)
    } finally {
      setMemoriesLoading(false)
    }
  }

  const handleStart = async (uid) => {
    setUserId(uid)
    await refreshMemories(uid)
  }

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || loading) return

    const userTurn = { role: 'user', content: msg }
    const newHistory = [...history, userTurn]
    setHistory(newHistory)
    setInput('')
    setLoading(true)

    try {
      const res = await sendMessage(userId, msg, history)
      const { reply } = res.data
      setHistory([...newHistory, { role: 'assistant', content: reply }])
      await refreshMemories()
    } catch (e) {
      setHistory([...newHistory, {
        role: 'assistant',
        content: '⚠️ Something went wrong. Is the backend running on port 8000?',
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleDeleteMemory = async (memId) => {
    try {
      await deleteMemory(userId, memId)
      setMemories(prev => prev.filter(m => m.id !== memId))
    } catch (e) {
      console.error('Delete failed', e)
    }
  }

  const handleDeleteAll = async () => {
    if (!confirm('Forget all memories for this user?')) return
    try {
      await deleteAllMemories(userId)
      setMemories([])
    } catch (e) {
      console.error('Delete all failed', e)
    }
  }

  // ── Setup screen ────────────────────────────────────────────────────────────
  if (!userId) return <UserSetup onStart={handleStart} />

  // ── Main chat UI ────────────────────────────────────────────────────────────
  return (
    <div className="h-screen bg-[#0a0a0f] flex flex-col overflow-hidden">

      {/* Top bar */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-md shadow-violet-500/20">
            <BrainIcon />
          </div>
          <div>
            <h1 className="text-white font-bold text-sm tracking-tight" style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}>
              MemChat
            </h1>
            <p className="text-zinc-500 text-xs">powered by Mem0</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-zinc-500 text-xs font-mono hidden sm:block">{userId}</span>
          <button
            onClick={() => setShowMemoryPanel(p => !p)}
            className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-all ${
              showMemoryPanel
                ? 'bg-violet-600/20 border-violet-500/50 text-violet-300'
                : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <BrainIcon />
            <span>Memory</span>
            {memories.length > 0 && (
              <span className="bg-violet-500 text-white text-xs px-1.5 rounded-full font-mono leading-none py-0.5">
                {memories.length}
              </span>
            )}
          </button>
          <button
            onClick={() => { setUserId(null); setHistory([]); setMemories([]) }}
            className="text-zinc-500 hover:text-zinc-300 text-xs transition-colors"
          >
            Switch user
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">

        {/* Chat area */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6">
            {history.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="text-5xl mb-4">🧠</div>
                <h2 className="text-white font-semibold text-lg mb-1" style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}>
                  Hey {userId}!
                </h2>
                <p className="text-zinc-400 text-sm max-w-sm">
                  I remember things across our conversations. Tell me about yourself, your preferences, or just ask anything.
                </p>
              </div>
            )}

            {history.map((msg, i) => (
              <ChatBubble key={i} msg={msg} />
            ))}

            {loading && (
              <div className="flex justify-start mb-4">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center mr-2 mt-0.5 flex-shrink-0">
                  <BrainIcon />
                </div>
                <div className="bg-zinc-800 border border-zinc-700 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1 items-center h-4">
                    <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-4 pb-4 flex-shrink-0">
            <div className="flex gap-2 bg-zinc-900 border border-zinc-700 rounded-2xl px-4 py-3 focus-within:border-violet-500 transition-all">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder="Message MemChat… (Enter to send, Shift+Enter for newline)"
                rows={1}
                className="flex-1 bg-transparent text-white text-sm placeholder-zinc-500 resize-none focus:outline-none leading-relaxed"
                style={{ maxHeight: '120px' }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="self-end bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white p-2 rounded-xl transition-all duration-200 flex-shrink-0"
              >
                {loading ? <SpinnerIcon /> : <SendIcon />}
              </button>
            </div>
            <p className="text-zinc-600 text-xs text-center mt-2">
              Memories are extracted and stored automatically after each reply.
            </p>
          </div>
        </div>

        {/* Memory panel */}
        {showMemoryPanel && (
          <div className="w-72 border-l border-zinc-800 bg-zinc-950/50 flex-shrink-0 flex flex-col overflow-hidden">
            <MemoryPanel
              userId={userId}
              memories={memories}
              loading={memoriesLoading}
              onDelete={handleDeleteMemory}
              onDeleteAll={handleDeleteAll}
              onRefresh={refreshMemories}
            />
          </div>
        )}
      </div>
    </div>
  )
}
