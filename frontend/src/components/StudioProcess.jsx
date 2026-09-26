import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Video,
  FileText,
  Cpu,
  Zap,
  MessageSquare,
  Mail,
  Shield,
  CheckCircle2,
  Terminal,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';

const ORBIT_NODES = [
  {
    id: 'ingestion',
    label: 'Transcript Ingestion',
    sublabel: 'Meet API / Notes',
    icon: Video,
    angle: -90, // 12 o'clock
    stageIds: ['classify_input', 'fetch_gmeet_transcript'],
  },
  {
    id: 'cross_analysis',
    label: 'Cross-Analysis',
    sublabel: 'Pattern Synthesis',
    icon: Cpu,
    angle: -30, // 2 o'clock
    stageIds: ['analyze_meetings'],
  },
  {
    id: 'stuck_topics',
    label: 'Stuck Topic Synthesis',
    sublabel: 'Blockers & Owners',
    icon: Zap,
    angle: 30, // 4 o'clock
    stageIds: ['extract_patterns', 'detect_stuck_topics'],
  },
  {
    id: 'slack_pulse',
    label: 'Slack Pulse',
    sublabel: 'Team Channel Broadcast',
    icon: MessageSquare,
    angle: 90, // 6 o'clock
    stageIds: ['post_slack_pulse'],
    tool: 'Slack',
  },
  {
    id: 'gmail_digest',
    label: 'Gmail Digest',
    sublabel: 'Manager Executive Email',
    icon: Mail,
    angle: 150, // 8 o'clock
    stageIds: ['send_gmail_digest'],
    tool: 'Gmail',
  },
  {
    id: 'notion_hub',
    label: 'Notion Hub',
    sublabel: 'Report & Decision Pages',
    icon: FileText,
    angle: 210, // 10 o'clock
    stageIds: ['write_notion_report', 'write_notion_decision_pages', 'write_notion_decision_page'],
    tool: 'Notion',
  },
];

export default function StudioProcess({ trace = [], isProcessing = false, onFinishReplay }) {
  const [activeOrbitId, setActiveOrbitId] = useState('ingestion');
  const [completedOrbitIds, setCompletedOrbitIds] = useState(new Set());
  const [logs, setLogs] = useState([
    { text: 'MeetLoop Agent connected to Swytchcode Policy Engine...', time: '00:01' },
    { text: 'Validating tool execution boundaries (tooling.json & policies.json)...', time: '00:02' },
  ]);
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Live in-flight progression while waiting for LLM & tool executions
  useEffect(() => {
    if (trace && trace.length > 0) return;

    const stages = ['ingestion', 'cross_analysis', 'stuck_topics', 'notion_hub', 'gmail_digest', 'slack_pulse'];
    let stageIdx = 0;

    const inFlightInterval = setInterval(() => {
      if (stageIdx < stages.length) {
        const stage = stages[stageIdx];
        setActiveOrbitId(stage);
        setCompletedOrbitIds((prev) => new Set(prev).add(stage));
        
        const stageLabels = {
          ingestion: 'Ingesting meeting transcript and tokenizing agenda items...',
          cross_analysis: 'Running multi-meeting cross-reasoning via OpenRouter LLM...',
          stuck_topics: 'Identifying recurring unowned tasks and commitment load...',
          notion_hub: 'Checking Swytchcode policy for Notion health report creation...',
          gmail_digest: 'Verifying manager recipient domain with Swytchcode guard...',
          slack_pulse: 'Formatting and validating team channel Slack pulse...',
        };

        setLogs((prev) => [
          ...prev,
          {
            text: `[${stage}] ${stageLabels[stage]}`,
            time: new Date().toLocaleTimeString().split(' ')[0],
          },
        ]);
        stageIdx++;
      } else {
        clearInterval(inFlightInterval);
      }
    }, 2200);

    return () => clearInterval(inFlightInterval);
  }, [trace]);

  // Replay live returned trace once completed
  useEffect(() => {
    if (!trace || trace.length === 0) return;

    let traceIdx = 0;
    const interval = setInterval(() => {
      if (traceIdx < trace.length) {
        const step = trace[traceIdx];
        const nodeName = step.node || step.node_name || '';
        const decision = step.decision || step.what_it_decided || '';
        const output = step.output_summary || '';

        // Match current trace node to corresponding orbital stage
        const matchedOrbit = ORBIT_NODES.find((n) => n.stageIds.includes(nodeName));
        if (matchedOrbit) {
          setActiveOrbitId(matchedOrbit.id);
          setCompletedOrbitIds((prev) => new Set(prev).add(matchedOrbit.id));
        }

        setLogs((prev) => [
          ...prev,
          {
            text: `[${nodeName}] ${decision}${output ? ` — ${output}` : ''}`,
            time: new Date().toLocaleTimeString().split(' ')[0],
          },
        ]);

        traceIdx++;
      } else {
        clearInterval(interval);
        setTimeout(() => {
          if (onFinishReplay) onFinishReplay();
        }, 900);
      }
    }, 600);

    return () => clearInterval(interval);
  }, [trace, onFinishReplay]);

  // Center coordinate and radius for orbital arrangement (520x520 canvas)
  const CENTER = 260;
  const RADIUS = 185;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full max-w-6xl mx-auto px-4 py-6"
    >
      {/* Top Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#EDE6D6]/10">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-[#D9A441] animate-ping" />
          <h2 className="font-display font-semibold text-lg sm:text-xl text-[#EDE6D6]">
            Auditing Cross-Meeting Intelligence...
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onFinishReplay}
            className="px-3.5 py-1.5 rounded-full bg-[#211C17] border border-[#EDE6D6]/20 text-xs font-mono text-[#D9A441] hover:bg-[#D9A441] hover:text-[#15120F] transition-all"
          >
            View Verdict & Exhibits →
          </button>
          <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-[#D9A441] bg-[#211C17] px-3.5 py-1.5 rounded-full border border-[#D9A441]/30 shadow-[0_0_15px_rgba(217,164,65,0.15)]">
            <Shield className="w-3.5 h-3.5 text-[#4F8F7A]" />
            <span>Swytchcode Policy: In-Flight Governance</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left / Center: Circular Orbital Stage Diagram (Matching Inspo) */}
        <div className="lg:col-span-7 flex flex-col items-center justify-center relative min-h-[540px] select-none">
          <div className="relative w-[520px] h-[520px] max-w-full flex items-center justify-center">
            {/* Orbital Concentric Rings */}
            <div className="absolute w-[440px] h-[440px] rounded-full border border-[#EDE6D6]/8 pointer-events-none" />
            <div className="absolute w-[370px] h-[370px] rounded-full border border-dashed border-[#EDE6D6]/12 pointer-events-none animate-spin-slow" />
            <div className="absolute w-[250px] h-[250px] rounded-full border border-[#EDE6D6]/6 pointer-events-none" />

            {/* SVG Spoke Laser Beams */}
            <svg
              viewBox="0 0 520 520"
              className="absolute inset-0 w-[520px] h-[520px] pointer-events-none z-10"
            >
              {ORBIT_NODES.map((node) => {
                const rad = (node.angle * Math.PI) / 180;
                const x = CENTER + Math.cos(rad) * RADIUS;
                const y = CENTER + Math.sin(rad) * RADIUS;
                const isActive = activeOrbitId === node.id;
                const isDone = completedOrbitIds.has(node.id) && !isActive;

                return (
                  <line
                    key={`spoke-${node.id}`}
                    x1={CENTER}
                    y1={CENTER}
                    x2={x}
                    y2={y}
                    stroke={isActive ? '#D9A441' : isDone ? '#4F8F7A' : 'rgba(237,230,214,0.12)'}
                    strokeWidth={isActive ? '2.5' : '1.5'}
                    strokeDasharray={isActive ? '5 5' : 'none'}
                    className={isActive ? 'animate-pulse' : ''}
                  />
                );
              })}
            </svg>

            {/* Central Hub (Relay / Policy Engine) */}
            <div
              className="absolute z-20 flex flex-col items-center justify-center -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${CENTER}px`, top: `${CENTER}px` }}
            >
              <motion.div
                animate={{
                  scale: [1, 1.04, 1],
                  boxShadow: [
                    '0 0 30px rgba(178,58,46,0.2)',
                    '0 0 50px rgba(217,164,65,0.35)',
                    '0 0 30px rgba(178,58,46,0.2)',
                  ],
                }}
                transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
                className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl bg-[#211C17] border border-[#EDE6D6]/20 flex flex-col items-center justify-center relative overflow-hidden backdrop-blur-xl"
              >
                {/* Internal atmospheric glow */}
                <div className="absolute inset-0 bg-gradient-to-tr from-[#B23A2E]/20 via-transparent to-[#D9A441]/20 pointer-events-none" />
                <Layers className="w-8 h-8 text-[#EDE6D6] mb-1 relative z-10" />
                <span className="text-[10px] font-mono tracking-wider uppercase text-[#D9A441] font-semibold relative z-10">
                  MEETLOOP
                </span>
              </motion.div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#EDE6D6]/60 mt-2 px-2.5 py-0.5 rounded-full bg-[#15120F] border border-[#EDE6D6]/10 shadow-sm">
                POLICY HUB
              </span>
            </div>

            {/* 6 Circular Orbital Nodes */}
            {ORBIT_NODES.map((node, idx) => {
              const rad = (node.angle * Math.PI) / 180;
              const nodeX = CENTER + Math.cos(rad) * RADIUS;
              const nodeY = CENTER + Math.sin(rad) * RADIUS;

              const isActive = activeOrbitId === node.id;
              const isDone = completedOrbitIds.has(node.id) && !isActive;
              const Icon = node.icon;

              return (
                <motion.div
                  key={node.id}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: isActive ? 1.1 : 1, opacity: 1 }}
                  transition={{ delay: idx * 0.06 }}
                  style={{
                    left: `${nodeX}px`,
                    top: `${nodeY}px`,
                  }}
                  className="absolute z-20 flex flex-col items-center justify-center -translate-x-1/2 -translate-y-1/2 cursor-pointer group pointer-events-auto"
                >
                  <div
                    className={`w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center border transition-all duration-300 ${
                      isActive
                        ? 'bg-[#211C17] border-[#D9A441] shadow-[0_0_30px_rgba(217,164,65,0.45)]'
                        : isDone
                        ? 'bg-[#15120F] border-[#4F8F7A]/70 shadow-[0_0_15px_rgba(79,143,122,0.25)]'
                        : 'bg-[#15120F]/90 border-[#EDE6D6]/15 opacity-60'
                    }`}
                  >
                    <Icon
                      className={`w-6 h-6 transition-colors ${
                        isActive
                          ? 'text-[#D9A441]'
                          : isDone
                          ? 'text-[#4F8F7A]'
                          : 'text-[#EDE6D6]/40'
                      }`}
                    />
                  </div>

                  {/* Node Label */}
                  <div className="mt-2 flex flex-col items-center text-center w-32">
                    <span
                      className={`text-[11px] font-ui font-medium tracking-tight ${
                        isActive
                          ? 'text-[#D9A441] font-semibold drop-shadow-sm'
                          : isDone
                          ? 'text-[#EDE6D6]'
                          : 'text-[#EDE6D6]/50'
                      }`}
                    >
                      {node.label}
                    </span>
                    <span className="text-[9px] font-mono text-[#EDE6D6]/40 whitespace-nowrap mt-0.5">
                      {isDone ? '✓ Verified' : node.sublabel}
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Right: Live Technical Trace Terminal */}
        <div className="lg:col-span-5 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#EDE6D6]/50 flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-[#D9A441]" /> Live Decision Audit Log
            </span>
            <span className="text-[10px] font-mono text-[#4F8F7A] bg-[#4F8F7A]/10 px-2 py-0.5 rounded-full border border-[#4F8F7A]/30">
              Live Stream
            </span>
          </div>

          <div className="flex-1 min-h-[380px] max-h-[460px] p-4 rounded-2xl bg-[#15120F] border border-[#EDE6D6]/12 font-mono text-xs overflow-y-auto flex flex-col shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
            <div className="flex flex-col gap-2.5">
              {logs.map((log, i) => (
                <div key={i} className="flex items-start gap-2 text-[#EDE6D6]/80 leading-relaxed">
                  <span className="text-[#D9A441]/70 text-[10px] select-none">{log.time}</span>
                  <span className="text-[#EDE6D6]/30 select-none">&gt;</span>
                  <span className="flex-1 text-[#EDE6D6]/90">{log.text}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
