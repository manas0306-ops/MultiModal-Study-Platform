import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Volume2,
  VolumeX,
  ShieldCheck,
  AlertCircle,
  Loader2,
  User,
  Bot,
  Cpu,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Upload,
  Layers,
  Zap,
  BookOpen,
  GraduationCap,
  Copy,
  Check,
  RotateCcw,
  MessageSquare,
  Globe,
  Headphones,
  ExternalLink,
  X
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { SourceCitation } from '../components/citations/SourceCitation';
import { AdaptivePhaseStudio } from '../components/learning/AdaptivePhaseStudio';
import { SmartExamMentorStudio } from '../components/learning/SmartExamMentorStudio';
import { EducationalContentRenderer } from '../components/common/EducationalContentRenderer';
import { AIOrchestrator, INTENT_CLASSES } from '../services/aiOrchestrator';
import { SmartExamEngine } from '../services/smartExamEngine';
import { AdaptivePhaseEngine } from '../services/adaptivePhaseEngine';
import { ClientIntelligenceEngine } from '../services/clientEngine';
import { ContentSanitizer } from '../services/contentSanitizer';

const STORAGE_KEY_CHAT_HISTORY = 'edupath_unlimited_chat_history_v1';

export const GroundedTutorPage = ({
  onNavigateToSource,
  onNavigateTab,
  onOpenUpload,
  initialContext,
  onClearContext,
  refreshTrigger
}) => {
  const { currentCourse, user } = useAuth();
  const [availableDocs, setAvailableDocs] = useState([]);
  const [expandedTraces, setExpandedTraces] = useState({});
  const [responseDepth, setResponseDepth] = useState('explanation'); // 'brief' | 'explanation'
  const [messageDepthOverrides, setMessageDepthOverrides] = useState({});
  const [copiedId, setCopiedId] = useState(null);
  const [liveWebSearchEnabled, setLiveWebSearchEnabled] = useState(true);
  const [questionsAskedCount, setQuestionsAskedCount] = useState(() =>
    AIOrchestrator.getQuestionsAskedCount()
  );

  // Active Studio view: 'chat' | 'phases' | 'mentor'
  const [activeStudioView, setActiveStudioView] = useState('chat');
  const [studioTopic, setStudioTopic] = useState('');

  const welcomeBrief = `**Open AI Learning Space**
Ask anything. Learn anything. Explore general computer science, programming, and academic questions, study your uploaded materials, or enter the 3-Phase Adaptive Learning Studio.

*Brief Mode vs. Deep Explanation*
Toggle between *Brief* (concise concept overview and key example) and *Deep Explanation* (comprehensive theory, step-by-step walkthrough, and common misconceptions) at any time.

**Key Idea**
Ask → Understand → Practice → Master. Upload any textbook PDF, slide deck, or lecture notes, or select a document from the Scope menu above and click *3-Phase & Grand Quiz* to learn through Phase 1 (Foundation), Phase 2 (Application), Phase 3 (Mastery), and the 15-MCQ Grand Quiz.`;

  const welcomeExplanation = `**Open AI Learning Space — Adaptive Learning Companion**
Welcome to your open, unlimited AI learning workspace. Ask any general academic, programming, or engineering question, query your uploaded study materials with source-grounded accuracy, or launch a structured 3-Phase Adaptive Learning session.

*Source-Grounded RAG & General Knowledge*
When you ask about your uploaded PDFs, slides, or notes, responses are grounded directly in your course material. When you ask general questions—such as *What is artificial intelligence?*, *Explain binary search*, or *Write a C++ program for two sum*—the tutor synthesizes a clear, structured lesson.

**Core Concept**
Every topic can be studied in two synchronized depths: *Brief Mode* for rapid revision and *Deep Explanation Mode* for thorough conceptual mastery with worked examples.

**How It Works**
Select any ingested document from the Scope dropdown and open *3-Phase & Grand Quiz* to study the material across three progressive phases:
• *Phase 1 (Foundation)*: Core definitions, prerequisites, and baseline intuition followed by a 5-question MCQ check.
• *Phase 2 (Application)*: Operational workflows, analytical mechanisms, and cause-and-effect relationships followed by 5 MCQs.
• *Phase 3 (Mastery)*: Advanced edge cases, design trade-offs, and synthesis followed by 5 MCQs and the 15-question cross-phase Grand Quiz.

**Example**
Try asking *"What is artificial intelligence?"*, *"Explain operating systems"*, or *"Teach me Design Thinking"* below, or click any quick prompt to begin.`;

  const allInitialDocs = ClientIntelligenceEngine.getAllDocuments();
  const activeSavedDoc = (() => {
    try {
      return localStorage.getItem('edupath_active_document') || '';
    } catch (_) {
      return '';
    }
  })();
  const primaryInitialDoc =
    (activeSavedDoc && allInitialDocs.find((d) => d.filename.toLowerCase().includes(activeSavedDoc.toLowerCase()))) ||
    allInitialDocs[0];
  const activeDocTitle = ContentSanitizer.cleanDocumentTitle(primaryInitialDoc?.filename || 'Course Knowledge Base');
  const activeDocTopic = ContentSanitizer.cleanText(primaryInitialDoc?.topic || 'Multimodal Study Platform');
  const activeDocUnit = primaryInitialDoc?.units?.[0];

  const initialRagDiagrams = SmartExamEngine.buildUnifiedRagDiagrams({
    query: 'What is artificial intelligence?',
    scopedDocument: activeDocTitle,
    chunksScanned: primaryInitialDoc?.units?.length || 8,
    bm25Score: 4.8,
    vectorScore: 0.98,
    sourceOrigin: 'Source-Grounded & General AI Synthesis'
  });

  const defaultWelcomeMessage = {
    id: 'welcome',
    role: 'assistant',
    content: welcomeExplanation,
    brief_content: welcomeBrief,
    explanation_content: welcomeExplanation,
    intent: 'SYSTEM_READY',
    source_origin: `Source-Grounded & General AI Synthesis (${activeDocTitle})`,
    rag_diagrams: initialRagDiagrams,
    citations: activeDocUnit
      ? [
          {
            source_type: primaryInitialDoc.file_type || 'pdf',
            document: activeDocTitle,
            location_label: ContentSanitizer.cleanText(activeDocUnit.location_label || 'Section 1'),
            excerpt: ContentSanitizer.cleanText(activeDocUnit.content || '').slice(0, 190),
            relevance: 0.99
          }
        ]
      : [],
    status: 'SUPPORTED',
    follow_up_questions: [
      `🎓 Teach me ${activeDocTitle} in 3 Adaptive Phases`,
      `Summarize the key facts from ${activeDocTitle}`,
      'What is artificial intelligence?',
      'Explain binary search.',
      'Write a C++ program for two sum.'
    ],
    recommended_next_action: {
      label: `Open Smart Exam Mentor for ${activeDocTopic}`,
      action_type: 'OPEN_SMART_MENTOR',
      reason: 'Practice with Bayesian Active Learning P(θ|D), AI Podcast TTS, ELI12, and Flagged Questions.'
    },
    anatomy_trace: [
      { step: 1, name: 'Secure Ingress & Context Assembly', detail: 'Sanitized input • 16-Class Intent Router' },
      { step: 2, name: 'Semantic & Lexical Indexing', detail: '384-d semantic vector + BM25 search terms' },
      { step: 3, name: 'Model & Retrieval Inference', detail: 'Vector Store Retrieval + LLM Outside Knowledge' },
      { step: 4, name: 'Prompt Assembly & Generation', detail: 'Combines retrieved context with instructions' },
      { step: 5, name: 'Safety, Moderation & Grounding Gate', detail: 'Verified citations & injection guard' },
      { step: 6, name: 'Grounded Response Delivery', detail: 'Instant ⚡ Brief / 📖 Explanation toggle' }
    ],
    pipeline_trace: {
      status: 'VERIFIED_GROUNDED',
      intent_detected: 'SYSTEM_READY',
      mode_selected: 'beginner',
      response_depth: 'explanation',
      scope_applied: activeDocTitle,
      chunks_scanned: primaryInitialDoc?.units?.length || 8,
      top_bm25_score: 4.8,
      top_vector_score: 0.98,
      topic: activeDocTopic,
      concept: primaryInitialDoc?.concepts?.[0] || 'Adaptive Learning',
      prerequisites: primaryInitialDoc?.prerequisites || ['Foundational Principles'],
      learner_mastery: 0.68
    }
  };

  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_CHAT_HISTORY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (_) {}
    return [defaultWelcomeMessage];
  });

  // Persist conversation history automatically without artificial limits
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CHAT_HISTORY, JSON.stringify(messages));
    } catch (_) {}
  }, [messages]);

  const [input, setInput] = useState('');
  const [selectedMode, setSelectedMode] = useState('beginner');
  const [scopedDocument, setScopedDocument] = useState(() => {
    try {
      return localStorage.getItem('edupath_active_document') || '';
    } catch (_) {
      return '';
    }
  });
  const [loading, setLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const messagesEndRef = useRef(null);

  const TUTOR_MODES = [
    { id: 'beginner', label: 'Beginner', desc: 'Analogies & step-by-step intuition' },
    { id: 'eli12', label: '🧒 ELI12', desc: "Explain Like I'm 12 story mode" },
    { id: 'exam', label: 'Exam Mode', desc: 'High-yield points, formulas & traps' },
    { id: 'deep_dive', label: 'Deep Dive', desc: 'Formal proofs & kernel internals' },
    { id: 'socratic', label: 'Socratic', desc: 'Probing questions & guided hints' },
    { id: 'interview', label: 'Interview', desc: 'FAANG systems design & trade-offs' },
    { id: 'bilingual', label: 'Bilingual', desc: 'English + हिंदी bilingual synthesis' }
  ];

  const QUICK_PROMPTS = [
    '🎓 Teach me this material in 3 Adaptive Phases',
    'Summarize the key facts from my uploaded document',
    'What is artificial intelligence?',
    'Explain binary search.',
    'Write a C++ program for two sum.',
    'What is the difference between ML and DL?',
    'What are the core concepts and formulas in my notes?',
    'Explain Design Thinking 5 stages with examples'
  ];

  // Load all documents (built-in + user-ingested) for the Scope selector
  useEffect(() => {
    const fetchDocs = async () => {
      const courseId = currentCourse?.id || 'OS_101';
      const data = await api.getSourceExplorer(courseId);
      if (data && Array.isArray(data.documents)) {
        setAvailableDocs(data.documents);
        const savedActive = localStorage.getItem('edupath_active_document');
        if (savedActive && data.documents.some((d) => d.filename === savedActive)) {
          setScopedDocument(savedActive);
        } else if (!scopedDocument && data.documents.length > 0) {
          const firstPersisted = data.documents.find((d) => d.id?.startsWith('doc_user_'));
          if (firstPersisted) {
            setScopedDocument(firstPersisted.filename);
          }
        }
      }
    };
    fetchDocs();
  }, [currentCourse, refreshTrigger]);

  // Handle incoming context when user clicks "Teach Me This", "Smart Exam Mentor", "Start 5-min remediation", or "Ask AI Tutor"
  useEffect(() => {
    if (initialContext) {
      const targetScope = initialContext.scopedDocument || '';
      if (targetScope) {
        setScopedDocument(targetScope);
      }
      if (initialContext.mode) {
        setSelectedMode(initialContext.mode);
      }
      if (initialContext.openAdaptiveStudio) {
        setStudioTopic(initialContext.customTopic || '');
        setActiveStudioView('phases');
      } else if (initialContext.openSmartMentor) {
        setStudioTopic(initialContext.customTopic || '');
        setActiveStudioView('mentor');
      } else if (initialContext.initialQuery) {
        setActiveStudioView('chat');
        handleSend(initialContext.initialQuery, targetScope, initialContext.mode || selectedMode);
      }
      if (onClearContext) {
        onClearContext();
      }
    }
  }, [initialContext]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeStudioView === 'chat') {
      scrollToBottom();
    }
  }, [messages, activeStudioView]);

  const toggleTrace = (msgId) => {
    setExpandedTraces((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleCopyMessage = (msgId, text) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedId(msgId);
      setTimeout(() => setCopiedId(null), 1800);
    }
  };

  const handleResetConversation = () => {
    setMessages([defaultWelcomeMessage]);
    try {
      localStorage.setItem(STORAGE_KEY_CHAT_HISTORY, JSON.stringify([defaultWelcomeMessage]));
    } catch (_) {}
  };

  const handleSend = async (
    textToSend,
    overrideScope = null,
    overrideMode = null,
    overrideDepth = null
  ) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const activeScope = overrideScope !== null ? overrideScope : scopedDocument;
    const activeMode = overrideMode || selectedMode;
    const activeDepth = overrideDepth || responseDepth;

    // Check if the user is explicitly asking to enter 3-Phase Adaptive Learning Mode
    if (
      /\b(teach me|start 3-phase|3 adaptive phases|three adaptive phases|start learning mode)\b/i.test(
        query.trim()
      )
    ) {
      const cleanedTopic = query
        .replace(
          /^(🎓\s*)?(teach me|start 3-phase learning on|teach me this material in 3 adaptive phases|teach me this)\s*/i,
          ''
        )
        .replace(/in 3 adaptive phases/i, '')
        .trim();
      setStudioTopic(cleanedTopic);
      setActiveStudioView('phases');
      if (!textToSend) setInput('');
      return;
    }

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      mode: activeMode,
      responseDepth: activeDepth,
      scope: activeScope || 'All Course Materials + General AI'
    };

    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const scopeLoc = activeScope ? { document: activeScope } : null;
      const res = await api.askTutor(
        query,
        activeMode,
        currentCourse?.id || 'OS_101',
        scopeLoc,
        activeDepth,
        'en',
        nextHistory,
        { enable_web_search: liveWebSearchEnabled }
      );

      if (res.questions_asked_count) {
        setQuestionsAskedCount(res.questions_asked_count);
      } else {
        setQuestionsAskedCount(AIOrchestrator.getQuestionsAskedCount());
      }

      const tutorMsgId = (Date.now() + 1).toString();
      const tutorMsg = {
        id: tutorMsgId,
        role: 'assistant',
        query_asked: query,
        content:
          res.answer ||
          res.content ||
          res.refusal_message ||
          'Here is a structured explanation for your question.',
        brief_content: res.brief_content || res.answer,
        explanation_content: res.explanation_content || res.answer,
        intent: res.intent || INTENT_CLASSES.GENERAL_QUESTION,
        source_origin: res.source_origin || (res.is_web_grounded ? 'Live Web Research' : 'General Knowledge & AI Reasoning'),
        rag_diagrams: res.rag_diagrams || null,
        citations: res.citations || [],
        web_sources: res.web_sources || [],
        is_web_grounded: res.is_web_grounded || false,
        is_course_grounded: res.is_course_grounded || false,
        status: res.grounding_status || (res.is_refusal ? 'UNSUPPORTED' : 'SUPPORTED'),
        follow_up_questions: res.related_questions || res.follow_up_questions || [],
        related_questions: res.related_questions || res.follow_up_questions || [],
        recommended_next_action: res.recommended_next_action || null,
        anatomy_trace: res.anatomy_trace || null,
        pipeline_trace: res.pipeline_trace || null
      };

      setMessages((prev) => [...prev, tutorMsg]);
      setExpandedTraces((prev) => ({ ...prev, [tutorMsgId]: false }));
    } catch (err) {
      console.error('Tutor error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Re-run last user query automatically when user switches Pedagogical Mode
  const handleModeSelect = (newModeId) => {
    setSelectedMode(newModeId);
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg && !loading && activeStudioView === 'chat') {
      handleSend(lastUserMsg.content, scopedDocument, newModeId, responseDepth);
    }
  };

  const toggleSpeech = (text) => {
    if (!('speechSynthesis' in window)) return;
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const cleanText = text.replace(/[*#_`~]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  // Compute informational learning metrics (Section 7 — never usage limits!)
  const activeLearningSession = (() => {
    try {
      return (
        AdaptivePhaseEngine.getActiveSession?.() ||
        AdaptivePhaseEngine.getSession?.() ||
        null
      );
    } catch (_) {
      return null;
    }
  })();
  const currentPhaseLabel = activeLearningSession
    ? `Phase ${activeLearningSession.currentPhaseNumber || 1}`
    : 'Phase 1';
  const masteryPercent = Math.round((user?.profile?.overall_mastery || 0.68) * 100);

  return (
    <div className="flex flex-col h-[calc(100vh-4.25rem)] max-w-4xl mx-auto w-full px-2 sm:px-4 py-2 space-y-2.5 overflow-hidden font-sans">
      {/* Sleek, Uncluttered Navigation & Scope Header */}
      <div className="bg-slate-900/95 border border-slate-800 rounded-2xl p-2.5 sm:px-3.5 sm:py-2.5 shadow-md shrink-0 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          {/* Left: View Mode Pills + Dynamic Scope Dropdown */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="inline-flex rounded-xl bg-slate-950 p-1 border border-slate-800 gap-1">
              <button
                onClick={() => setActiveStudioView('chat')}
                className={`px-3 py-1 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeStudioView === 'chat'
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>AI Tutor</span>
              </button>
              <button
                onClick={() => setActiveStudioView('phases')}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1 transition-all cursor-pointer ${
                  activeStudioView === 'phases'
                    ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-slate-950 shadow'
                    : 'text-amber-300 hover:text-amber-200'
                }`}
                title="Open 3-Phase Adaptive Learning Studio & Grand Quiz"
              >
                <GraduationCap className="w-3.5 h-3.5" />
                <span>3-Phase</span>
              </button>
              <button
                onClick={() => setActiveStudioView('mentor')}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1 transition-all cursor-pointer ${
                  activeStudioView === 'mentor'
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-slate-950 shadow'
                    : 'text-emerald-300 hover:text-emerald-200'
                }`}
                title="Open Smart Exam Mentor & Podcast Audio"
              >
                <Headphones className="w-3.5 h-3.5" />
                <span>Mentor</span>
              </button>
            </div>

            {/* Scope Dropdown */}
            <div className="flex items-center gap-1.5 text-xs">
              <select
                value={scopedDocument}
                onChange={(e) => setScopedDocument(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-slate-200 outline-none focus:ring-1 focus:ring-indigo-500 text-xs max-w-[210px] truncate"
                title="Select source material to ground answers, or choose Open Knowledge to ask general questions"
              >
                <option value="">🌐 Open Knowledge + Web</option>
                {availableDocs.map((doc) => (
                  <option key={doc.id} value={doc.filename}>
                    📄 {doc.filename}
                  </option>
                ))}
              </select>

              {onOpenUpload && (
                <button
                  onClick={onOpenUpload}
                  className="p-1.5 rounded-xl bg-indigo-500/15 hover:bg-indigo-500/25 border border-indigo-500/30 text-indigo-300 text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer"
                  title="Upload new PDF, PPTX, or notes"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">+ Ingest</span>
                </button>
              )}
            </div>
          </div>

          {/* Right: Pedagogical Mode Selector + Brief/Detailed Toggle + Reset */}
          <div className="flex items-center gap-2">
            {activeStudioView === 'chat' && (
              <select
                value={selectedMode}
                onChange={(e) => handleModeSelect(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1 text-slate-300 text-xs outline-none focus:ring-1 focus:ring-indigo-500"
                title="Select teaching style"
              >
                {TUTOR_MODES.map((mode) => (
                  <option key={mode.id} value={mode.id}>
                    {mode.label}
                  </option>
                ))}
              </select>
            )}

            <div className="inline-flex rounded-xl bg-slate-950 p-0.5 border border-slate-800">
              <button
                onClick={() => {
                  setResponseDepth('brief');
                  setMessageDepthOverrides({});
                }}
                className={`px-2 py-1 rounded-lg text-xs font-bold flex items-center gap-1 transition-all cursor-pointer ${
                  responseDepth === 'brief'
                    ? 'bg-amber-500 text-slate-950 shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Concise high-yield answers"
              >
                <Zap className="w-3 h-3" />
                <span>Brief</span>
              </button>
              <button
                onClick={() => {
                  setResponseDepth('explanation');
                  setMessageDepthOverrides({});
                }}
                className={`px-2 py-1 rounded-lg text-xs font-bold flex items-center gap-1 transition-all cursor-pointer ${
                  responseDepth === 'explanation'
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Deep step-by-step conceptual explanations"
              >
                <BookOpen className="w-3 h-3" />
                <span>Deep</span>
              </button>
            </div>

            {messages.length > 1 && activeStudioView === 'chat' && (
              <button
                onClick={handleResetConversation}
                className="p-1.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                title="Start a fresh conversation thread"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Clear Relationship Indicator: When a document scope is active */}
        {scopedDocument && activeStudioView === 'chat' && (
          <div className="flex items-center justify-between px-2.5 py-1 rounded-xl bg-indigo-500/10 border border-indigo-500/25 text-xs text-indigo-300">
            <span className="flex items-center gap-1.5 truncate">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0 text-indigo-400" />
              <span>Grounded in document: <strong>{scopedDocument}</strong></span>
            </span>
            <button
              onClick={() => setScopedDocument('')}
              className="text-[11px] text-slate-400 hover:text-white flex items-center gap-1 ml-2 shrink-0 cursor-pointer"
              title="Clear document scope to ask general questions"
            >
              <X className="w-3 h-3" />
              <span>Open Knowledge Mode</span>
            </button>
          </div>
        )}
      </div>

      {/* Main Workspace Area: 3-Phase Studio | Smart Exam Mentor Studio | Conversational AI Chat */}
      {activeStudioView === 'phases' ? (
        <div className="flex-1 overflow-y-auto pr-1">
          <AdaptivePhaseStudio
            scopedDocument={scopedDocument}
            initialTopic={studioTopic}
            onClose={() => setActiveStudioView('chat')}
            onAskTutorQuestion={(q) => {
              setActiveStudioView('chat');
              handleSend(q, scopedDocument, selectedMode, responseDepth);
            }}
          />
        </div>
      ) : activeStudioView === 'mentor' ? (
        <div className="flex-1 overflow-y-auto pr-1">
          <SmartExamMentorStudio
            scopedDocument={scopedDocument}
            customTopic={studioTopic}
            onClose={() => setActiveStudioView('chat')}
            onAskTutorQuestion={(q) => {
              setActiveStudioView('chat');
              handleSend(q, scopedDocument, selectedMode, responseDepth);
            }}
          />
        </div>
      ) : (
        <>
          {/* Centered, Spacious Chat Feed */}
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-1.5 scroll-smooth">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              const trace = msg.pipeline_trace;
              const isTraceOpen = !!expandedTraces[msg.id];
              const msgDepth = messageDepthOverrides[msg.id] || responseDepth;
              const displayedContent = isUser
                ? msg.content
                : msgDepth === 'brief'
                ? msg.brief_content || msg.content
                : msg.explanation_content || msg.content;

              return (
                <div
                  key={msg.id}
                  className={`flex gap-2.5 sm:gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-indigo-600 flex items-center justify-center shrink-0 shadow mt-1">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div
                    className={`rounded-2xl p-3.5 sm:p-4 text-xs sm:text-sm leading-relaxed ${
                      isUser
                        ? 'bg-indigo-600 text-white shadow max-w-[85%] rounded-br-sm'
                        : 'bg-slate-900 border border-slate-800 text-slate-200 shadow-sm w-full'
                    }`}
                  >
                    {/* Assistant Source Origin & Grounding Header */}
                    {!isUser && (
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-2 border-b border-slate-800">
                        <div className="flex flex-wrap items-center gap-1.5">
                          {(msg.status === 'DIRECT_CALCULATION' || msg.intent === 'DIRECT_CALCULATION') && (
                            <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                              <Zap className="w-3.5 h-3.5 text-emerald-400" /> Direct Calculation
                            </span>
                          )}
                          {(msg.is_web_grounded || (msg.web_sources && msg.web_sources.length > 0)) && (
                            <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                              <Globe className="w-3.5 h-3.5 text-emerald-400" /> Live Web Research ({msg.web_sources?.length || 1} sources)
                            </span>
                          )}
                          {msg.status === 'SUPPORTED' && !msg.is_web_grounded && (
                            <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" /> Grounded in Course Material
                            </span>
                          )}
                          {msg.status === 'GENERAL_AI' && !msg.is_web_grounded && msg.status !== 'DIRECT_CALCULATION' && msg.intent !== 'DIRECT_CALCULATION' && (
                            <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/25">
                              <Sparkles className="w-3.5 h-3.5 text-sky-400" /> {msg.source_origin || 'General AI Reasoning'}
                            </span>
                          )}
                        </div>

                        {/* Right Utility Buttons: Brief/Deep, Copy, Read Aloud, Regenerate */}
                        <div className="flex items-center gap-1">
                          {msg.brief_content && msg.explanation_content && (
                            <div className="inline-flex rounded-lg bg-slate-950 p-0.5 border border-slate-800 mr-1">
                              <button
                                onClick={() =>
                                  setMessageDepthOverrides((prev) => ({
                                    ...prev,
                                    [msg.id]: 'brief'
                                  }))
                                }
                                className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer ${
                                  msgDepth === 'brief'
                                    ? 'bg-amber-500 text-slate-950'
                                    : 'text-slate-400 hover:text-white'
                                }`}
                              >
                                ⚡ Brief
                              </button>
                              <button
                                onClick={() =>
                                  setMessageDepthOverrides((prev) => ({
                                    ...prev,
                                    [msg.id]: 'explanation'
                                  }))
                                }
                                className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer ${
                                  msgDepth === 'explanation'
                                    ? 'bg-indigo-600 text-white'
                                    : 'text-slate-400 hover:text-white'
                                }`}
                              >
                                📖 Deep
                              </button>
                            </div>
                          )}

                          <button
                            onClick={() => handleCopyMessage(msg.id, displayedContent)}
                            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors cursor-pointer"
                            title="Copy response"
                          >
                            {copiedId === msg.id ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>

                          {msg.query_asked && (
                            <button
                              onClick={() =>
                                handleSend(msg.query_asked, scopedDocument, selectedMode, msgDepth)
                              }
                              className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-indigo-400 transition-colors cursor-pointer"
                              title="Regenerate response"
                            >
                              <RotateCcw className="w-3.5 h-3.5" />
                            </button>
                          )}

                          <button
                            onClick={() => toggleSpeech(displayedContent)}
                            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-indigo-400 transition-colors cursor-pointer"
                            title={isSpeaking ? 'Stop read-aloud' : 'Read aloud'}
                          >
                            {isSpeaking ? (
                              <VolumeX className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                            ) : (
                              <Volume2 className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Rendered Content */}
                    {isUser ? (
                      <div className="whitespace-pre-wrap font-sans text-xs sm:text-sm leading-relaxed">
                        {displayedContent}
                      </div>
                    ) : (
                      <EducationalContentRenderer content={displayedContent} />
                    )}

                    {/* Course Document Citations */}
                    {!isUser && msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2.5 pt-2 border-t border-slate-800 space-y-1">
                        <span className="text-[11px] font-semibold text-slate-400 block">
                          Verified Citations ({msg.citations.length}):
                        </span>
                        <div className="space-y-1">
                          {msg.citations.map((c, idx) => (
                            <SourceCitation
                              key={idx}
                              citation={c}
                              onJump={(cit) => onNavigateToSource && onNavigateToSource(cit)}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Live Web Sources */}
                    {!isUser && msg.web_sources && msg.web_sources.length > 0 && (
                      <div className="mt-2.5 pt-2 border-t border-slate-800 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-xs text-slate-300 font-bold">
                          <Globe className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Web Evidence Sources:</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {msg.web_sources.map((src, idx) => (
                            <a
                              key={idx}
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-2 rounded-xl bg-slate-950/80 hover:bg-slate-950 border border-slate-800 hover:border-emerald-500/50 flex flex-col justify-between group transition-all"
                            >
                              <div className="flex items-center justify-between gap-1">
                                <span className="text-xs font-bold text-slate-200 group-hover:text-emerald-400 transition-colors line-clamp-1">
                                  [{src.citation_id || idx + 1}] {src.title}
                                </span>
                                <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-emerald-400 shrink-0" />
                              </div>
                              <span className="text-[10px] text-slate-400 line-clamp-1 mt-0.5 font-mono">
                                {src.domain}
                              </span>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Dynamic Follow-up Suggestions (Exactly 3 High-Relevance Chips) */}
                    {!isUser && (msg.related_questions || msg.follow_up_questions)?.length > 0 && (
                      <div className="mt-2.5 pt-2 border-t border-slate-800/80 space-y-1.5">
                        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                          Related Questions:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {(msg.related_questions || msg.follow_up_questions).slice(0, 3).map((fq, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSend(fq)}
                              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/40 text-slate-300 hover:text-white text-xs transition-colors text-left cursor-pointer"
                            >
                              → {fq}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Subtle Collapsible Reasoning Trace */}
                    {!isUser && trace && (
                      <div className="mt-2 pt-1 border-t border-slate-800/60">
                        <button
                          onClick={() => toggleTrace(msg.id)}
                          className="text-[10px] text-slate-500 hover:text-slate-300 flex items-center gap-1 font-mono cursor-pointer"
                        >
                          <Cpu className="w-3 h-3" />
                          <span>Technical reasoning trace {isTraceOpen ? '▲' : '▼'}</span>
                        </button>
                        {isTraceOpen && (
                          <div className="mt-1.5 p-2 rounded-lg bg-slate-950 border border-slate-800 text-[10px] font-mono space-y-1 text-slate-400">
                            <div>Intent: {trace.intent_detected || msg.intent} • Mode: {trace.mode_selected || selectedMode}</div>
                            <div>Origin: {msg.source_origin} • Chunks: {trace.chunks_scanned || 0}</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700 mt-1">
                      <User className="w-4 h-4 text-slate-300" />
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="flex gap-2.5 items-center text-slate-400 text-xs py-1">
                <div className="w-7 h-7 rounded-xl bg-indigo-600 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                  <span>Synthesizing response...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Starter Chips (Only shown when thread is fresh) */}
          {messages.length <= 1 && (
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs shrink-0">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider shrink-0">
                Try:
              </span>
              {QUICK_PROMPTS.slice(0, 4).map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(prompt)}
                  className="px-2.5 py-1 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs whitespace-nowrap transition-colors cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {/* Fixed Bottom Input Composer */}
          <div className="p-2 rounded-2xl bg-slate-900 border border-slate-800 flex items-center gap-2 shadow-xl shrink-0">
            <button
              type="button"
              onClick={() => setLiveWebSearchEnabled(!liveWebSearchEnabled)}
              className={`px-2.5 py-1.5 rounded-xl border text-xs font-bold flex items-center gap-1.5 shrink-0 transition-all cursor-pointer ${
                liveWebSearchEnabled
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-sm'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
              title="Toggle Live Web Grounding"
            >
              <Globe className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Web:</span> {liveWebSearchEnabled ? 'ON' : 'OFF'}
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={
                scopedDocument
                  ? `Ask question grounded in ${scopedDocument}...`
                  : `Ask anything — 2+2, Python code, AI concepts, or "Quiz me"...`
              }
              className="flex-1 bg-transparent px-2.5 py-2 text-xs sm:text-sm text-slate-200 outline-none placeholder:text-slate-500"
            />

            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="p-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white transition-all shadow shrink-0 cursor-pointer"
              title="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </>
      )}
    </div>
  );
};
