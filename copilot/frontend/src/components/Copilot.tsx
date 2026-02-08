import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, Database, AlertTriangle, CheckCircle, Loader2, Code, ChevronDown, ChevronUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface ThinkingStep {
  id: string
  title: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
  sql?: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  intent?: string
  alert_level?: string
  timestamp: Date
  thinkingSteps?: ThinkingStep[]
  isStreaming?: boolean
  persona?: { name: string; emoji: string }
}

interface CopilotProps {
  onWorkOrderCreated?: () => void
}

const PERSONA_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  'Vegetation Guardian': { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/30' },
  'Asset Inspector': { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
  'Fire Risk Analyst': { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' },
  'Water Treeing Detective': { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' },
}

const SUGGESTED_QUESTIONS = [
  "What's the hidden discovery?",
  "Show critical risk assets",
  "Vegetation compliance status",
  "Which circuits are PSPS candidates?",
  "Water treeing analysis",
  "Fire season readiness",
]

export function Copilot({ onWorkOrderCreated }: CopilotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `👋 Hello! I'm **VIGIL**, your Wildfire Risk Intelligence co-pilot.

I can help you analyze your asset portfolio and identify hidden risks. Ask me about:

- 🔥 **Fire risk** and PSPS candidates
- 🌲 **Vegetation** compliance and trimming priorities
- ⚡ **Asset health** and replacement needs
- 🔍 **Hidden patterns** in underground cables (my specialty!)

Try asking: *"What's the hidden discovery?"*`,
      sources: [],
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showThinking, setShowThinking] = useState<Record<string, boolean>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessageWithStream = async (content: string) => {
    if (!content.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    const assistantId = (Date.now() + 1).toString()
    
    const initialAssistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      thinkingSteps: [],
      isStreaming: true,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, initialAssistantMessage])
    setShowThinking(prev => ({ ...prev, [assistantId]: true }))

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content.trim()
        })
      })

      if (!response.ok || !response.body) {
        throw new Error('Streaming not available')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullContent = ''
      const thinkingSteps: ThinkingStep[] = []
      let sources: string[] = []
      let persona: { name: string; emoji: string } | undefined

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const eventStr of events) {
          if (!eventStr.trim() || !eventStr.startsWith('data:')) continue
          
          const dataStr = eventStr.replace('data:', '').trim()
          if (dataStr === '[DONE]') continue

          try {
            const event = JSON.parse(dataStr)
            
            if (event.type === 'text') {
              fullContent += event.content || ''
              setMessages(prev => prev.map(msg => 
                msg.id === assistantId 
                  ? { ...msg, content: fullContent }
                  : msg
              ))
            } else if (event.type === 'thinking') {
              const thinkingText = event.content || ''
              if (thinkingText.length > 20) {
                const step: ThinkingStep = {
                  id: `step-${Date.now()}`,
                  title: event.title || 'Reasoning',
                  content: thinkingText.slice(0, 200) + (thinkingText.length > 200 ? '...' : ''),
                  status: 'in_progress',
                  sql: event.sql
                }
                if (thinkingSteps.length >= 5) {
                  thinkingSteps.shift()
                }
                thinkingSteps.push(step)
                thinkingSteps.slice(0, -1).forEach(s => s.status = 'completed')
                
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantId 
                    ? { ...msg, thinkingSteps: [...thinkingSteps] }
                    : msg
                ))
              }
            } else if (event.type === 'status' || event.type === 'tool_status') {
              const step: ThinkingStep = {
                id: `status-${Date.now()}`,
                title: event.title || event.status || 'Processing',
                content: event.content || '',
                status: 'in_progress'
              }
              thinkingSteps.push(step)
              thinkingSteps.slice(0, -1).forEach(s => s.status = 'completed')
              
              setMessages(prev => prev.map(msg => 
                msg.id === assistantId 
                  ? { ...msg, thinkingSteps: [...thinkingSteps] }
                  : msg
              ))
            } else if (event.type === 'tool_result') {
              if (event.sql) {
                const sqlStep: ThinkingStep = {
                  id: `sql-${Date.now()}`,
                  title: 'SQL Executed',
                  content: event.error || 'Query completed',
                  status: event.error ? 'pending' : 'completed',
                  sql: event.sql
                }
                thinkingSteps.push(sqlStep)
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantId 
                    ? { ...msg, thinkingSteps: [...thinkingSteps] }
                    : msg
                ))
              }
            } else if (event.type === 'sources') {
              sources = event.sources || []
            } else if (event.type === 'persona') {
              persona = event.persona
              setMessages(prev => prev.map(msg => 
                msg.id === assistantId 
                  ? { ...msg, persona }
                  : msg
              ))
            } else if (event.type === 'error') {
              fullContent += `\n\n⚠️ ${event.content || 'An error occurred'}`
              setMessages(prev => prev.map(msg => 
                msg.id === assistantId 
                  ? { ...msg, content: fullContent }
                  : msg
              ))
            } else if (event.type === 'done') {
              if (event.work_order_created && onWorkOrderCreated) {
                onWorkOrderCreated()
              }
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }

      thinkingSteps.forEach(s => s.status = 'completed')
      
      setMessages(prev => prev.map(msg => 
        msg.id === assistantId 
          ? { 
              ...msg, 
              content: fullContent || 'I processed your request.',
              thinkingSteps: [...thinkingSteps],
              sources,
              persona,
              isStreaming: false 
            }
          : msg
      ))

      setTimeout(() => {
        setShowThinking(prev => ({ ...prev, [assistantId]: false }))
      }, 2000)

    } catch (error) {
      console.log('Streaming failed, falling back to local:', error)
      
      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content.trim()
          })
        })

        if (!response.ok) throw new Error('Failed to get response')

        const data = await response.json()
        
        setMessages(prev => prev.map(msg => 
          msg.id === assistantId 
            ? { 
                ...msg, 
                content: data.message || data.response,
                sources: data.sources,
                intent: data.intent,
                alert_level: data.alert_level,
                persona: data.persona,
                isStreaming: false,
                thinkingSteps: [
                  { id: 'step-1', title: 'Understanding Query', content: 'Analyzed your question', status: 'completed' as const },
                  { id: 'step-2', title: 'Querying Snowflake', content: 'Retrieved data from warehouse', status: 'completed' as const },
                  { id: 'step-3', title: 'Analyzing Results', content: 'Processing risk data', status: 'completed' as const },
                ]
              }
            : msg
        ))

        if (data.work_order_created && onWorkOrderCreated) {
          onWorkOrderCreated()
        }
      } catch (fallbackError) {
        console.error('Chat error:', fallbackError)
        setMessages(prev => prev.map(msg => 
          msg.id === assistantId 
            ? { 
                ...msg, 
                content: 'I encountered an error. Please try rephrasing your question.',
                isStreaming: false 
              }
            : msg
        ))
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessageWithStream(input)
  }

  const toggleThinking = (messageId: string) => {
    setShowThinking(prev => ({ ...prev, [messageId]: !prev[messageId] }))
  }

  return (
    <div className="flex flex-col h-full bg-gray-900">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div 
            key={message.id}
            className={`flex gap-3 ${
              message.role === 'user' ? 'justify-end' : ''
            }`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
            )}
            
            <div className={`max-w-[85%] ${message.role === 'user' ? 'order-first' : ''}`}>
              {message.role === 'assistant' && message.thinkingSteps && message.thinkingSteps.length > 0 && (
                <div className="mb-2">
                  <button
                    onClick={() => toggleThinking(message.id)}
                    className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-300 transition-colors mb-1"
                  >
                    <span className="flex items-center gap-1">
                      {message.isStreaming ? (
                        <Loader2 size={12} className="animate-spin text-purple-500" />
                      ) : (
                        <CheckCircle size={12} className="text-green-500" />
                      )}
                      <span>Thinking steps ({message.thinkingSteps.length})</span>
                    </span>
                    {showThinking[message.id] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  </button>
                  
                  {showThinking[message.id] && (
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3 space-y-2">
                      {message.thinkingSteps.map((step) => (
                        <div key={step.id} className="flex items-start gap-2">
                          {step.status === 'completed' ? (
                            <CheckCircle size={14} className="text-green-500 mt-0.5 flex-shrink-0" />
                          ) : step.status === 'in_progress' ? (
                            <Loader2 size={14} className="animate-spin text-purple-500 mt-0.5 flex-shrink-0" />
                          ) : (
                            <div className="w-3.5 h-3.5 rounded-full border border-slate-600 mt-0.5 flex-shrink-0" />
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-slate-300">{step.title}</div>
                            {step.content && (
                              <div className="text-xs text-slate-500">{step.content}</div>
                            )}
                            {step.sql && (
                              <div className="mt-1 p-2 bg-gray-800 rounded text-xs font-mono text-slate-400 overflow-x-auto">
                                <div className="flex items-center gap-1 text-purple-400 mb-1">
                                  <Code size={10} />
                                  <span>SQL</span>
                                </div>
                                <pre className="whitespace-pre-wrap break-all">{step.sql.slice(0, 200)}...</pre>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {message.role === 'assistant' && message.persona && (
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-0.5 rounded-full text-xs border ${
                    PERSONA_STYLES[message.persona.name]?.bg || 'bg-purple-500/10'
                  } ${PERSONA_STYLES[message.persona.name]?.text || 'text-purple-400'} ${
                    PERSONA_STYLES[message.persona.name]?.border || 'border-purple-500/30'
                  }`}>
                    {message.persona.emoji} {message.persona.name}
                  </span>
                </div>
              )}

              <div 
                className={`rounded-lg p-4 ${
                  message.role === 'user' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-800 border border-gray-700/50'
                }`}
              >
                {message.role === 'assistant' ? (
                  <div className="prose prose-invert prose-sm max-w-none">
                    {message.isStreaming && !message.content ? (
                      <div className="flex items-center gap-2 text-slate-400">
                        <Loader2 size={14} className="animate-spin" />
                        <span>Processing...</span>
                      </div>
                    ) : (
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    )}
                  </div>
                ) : (
                  <p>{message.content}</p>
                )}
              </div>
              
              {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <Database size={12} />
                  <span>Sources:</span>
                  {message.sources.map((source, i) => (
                    <span key={i} className="px-2 py-0.5 bg-gray-700 rounded text-slate-400">
                      {source}
                    </span>
                  ))}
                </div>
              )}

              {message.alert_level === 'high' && (
                <div className="mt-2 flex items-center gap-2 text-xs text-yellow-400">
                  <AlertTriangle size={12} />
                  <span>High-priority insight detected</span>
                </div>
              )}
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gray-600 flex items-center justify-center">
                <User size={16} className="text-slate-300" />
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {messages.length <= 2 && (
        <div className="px-4 pb-2">
          <div className="flex items-center gap-2 mb-2 text-xs text-slate-500">
            <Sparkles size={12} />
            <span>Suggested questions</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.slice(0, 4).map((q, i) => (
              <button
                key={i}
                onClick={() => sendMessageWithStream(q)}
                className="px-3 py-1.5 bg-gray-700/50 hover:bg-gray-600/50 rounded-full text-xs text-slate-300 hover:text-white transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700/50">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask VIGIL anything..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-purple-500 transition-colors"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  )
}
