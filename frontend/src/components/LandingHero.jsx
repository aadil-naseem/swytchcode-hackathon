import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Play, Shield, Sparkles, FileText, CheckCircle2, MessageSquare, Mail } from 'lucide-react';
import Particles from './reactbits/Particles';

export default function LandingHero({ onStartAudit, onQuickDemo }) {
  const [hoveredFragment, setHoveredFragment] = useState(null);

  // Scattered meeting fragments pinned around the investigation room
  const fragments = [
    {
      id: 'f1',
      text: '"...let\'s revisit pricing tiers next week..."',
      meeting: 'Tuesday Standup',
      pos: 'top-[18%] left-[5%] md:left-[8%]',
      rotation: '-rotate-3',
      connected: true,
    },
    {
      id: 'f2',
      text: '"...Arjun, can you also take the sales survey?..."',
      meeting: 'Sprint Planning',
      pos: 'bottom-[22%] left-[4%] md:left-[7%]',
      rotation: 'rotate-2',
      connected: false,
    },
    {
      id: 'f3',
      text: '"...still waiting on executive approval for seat pricing..."',
      meeting: 'Thursday Exec Review',
      pos: 'top-[22%] right-[5%] md:right-[8%]',
      rotation: 'rotate-3',
      connected: true,
    },
    {
      id: 'f4',
      text: '"...onboarding schema change blocked on UX names..."',
      meeting: 'Product Sync',
      pos: 'bottom-[20%] right-[4%] md:right-[7%]',
      rotation: '-rotate-2',
      connected: false,
    },
  ];

  return (
    <div className="relative min-h-screen w-full flex flex-col items-center justify-between px-6 py-10 overflow-hidden bg-[#15120F] select-none">
      {/* 1. Ambient Background Particles */}
      <Particles
        particleCount={35}
        speed={0.2}
        particleColors={['#B23A2E', '#D9A441', '#EDE6D6']}
        alpha={0.3}
        className="opacity-40"
      />

      {/* Atmospheric Radial Gradients (Inspo Glow) */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-[#B23A2E]/10 via-[#4F8F7A]/10 to-[#D9A441]/10 blur-[130px] opacity-70 animate-pulse" />
      </div>

      {/* 2. Top Header / Brand Nav */}
      <motion.header
        initial={{ opacity: 0, y: -15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-20 w-full max-w-6xl flex items-center justify-between pt-2"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#B23A2E]/20 border border-[#B23A2E]/40 flex items-center justify-center shadow-[0_0_15px_rgba(178,58,46,0.3)]">
            <div className="w-3 h-3 rounded-full bg-[#B23A2E]" />
          </div>
          <span className="font-display font-semibold text-xl tracking-tight text-[#EDE6D6]">
            MeetLoop
          </span>
          <span className="text-[11px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-[#211C17] border border-[#EDE6D6]/10 text-[#D9A441]">
            Swytchcode AI
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-[#EDE6D6]/60 bg-[#211C17]/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-[#EDE6D6]/10">
            <span className="w-2 h-2 rounded-full bg-[#4F8F7A] animate-ping" />
            Policy Engine: Active
          </div>
        </div>
      </motion.header>

      {/* 3. Floating Investigation Fragments (Desktop) */}
      <div className="hidden lg:block pointer-events-none absolute inset-0 z-10 max-w-7xl mx-auto">
        {fragments.map((frag, idx) => (
          <motion.div
            key={frag.id}
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 + idx * 0.15 }}
            className={`pointer-events-auto absolute ${frag.pos} ${frag.rotation} transition-all duration-300 hover:scale-105 hover:z-30`}
            onMouseEnter={() => setHoveredFragment(frag.id)}
            onMouseLeave={() => setHoveredFragment(null)}
          >
            <div className="w-56 p-3.5 rounded-xl bg-[#211C17]/85 backdrop-blur-md border border-[#EDE6D6]/12 shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#D9A441]">
                  {frag.meeting}
                </span>
                <span className="text-[9px] font-mono text-[#EDE6D6]/40">Fragment #{idx + 1}</span>
              </div>
              <p className="text-xs text-[#EDE6D6]/85 font-mono leading-relaxed line-clamp-2">
                {frag.text}
              </p>
              {frag.connected && (
                <div className="mt-2 pt-1.5 border-t border-[#EDE6D6]/8 flex items-center gap-1.5 text-[10px] font-mono text-[#B23A2E]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#B23A2E]" />
                  Unresolved thread detected
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* 4. Centerpiece Hero (Matching Inspo) */}
      <div className="relative z-20 max-w-3xl mx-auto text-center flex flex-col items-center justify-center my-auto py-12">
        {/* Glowing Orb Component */}
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className="relative mb-6 flex items-center justify-center cursor-pointer group"
          onClick={onStartAudit}
        >
          {/* Outer Iridescent Halo */}
          <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-[#9B51E0] via-[#38E8C6] to-[#FFA07A] p-[2px] shadow-[0_0_50px_rgba(217,164,65,0.35),0_0_80px_rgba(178,58,46,0.25)] animate-spin-slow">
            {/* Inner Dark Lens */}
            <div className="w-full h-full rounded-full bg-[#15120F] flex items-center justify-center relative overflow-hidden">
              {/* Internal Glow Reflection */}
              <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent opacity-60 rounded-full" />
              {/* Center Pulsing White Iris */}
              <div className="w-3.5 h-3.5 rounded-full bg-[#EDE6D6] shadow-[0_0_12px_#FFF] group-hover:scale-125 transition-transform duration-300" />
            </div>
          </div>
        </motion.div>

        {/* Subtitle Badge */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-4"
        >
          <span className="text-xs md:text-sm font-ui tracking-wide text-[#EDE6D6]/70 font-medium">
            MeetLoop Intelligence
          </span>
        </motion.div>

        {/* Massive Dual-Tier Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="text-4xl sm:text-5xl md:text-6xl font-display font-semibold tracking-tight leading-[1.1] mb-6 text-[#EDE6D6]"
        >
          One calm intelligence <br />
          <span className="text-[#EDE6D6]/40 font-normal">between every meeting.</span>
        </motion.h1>

        {/* Crisp Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="max-w-xl text-sm sm:text-base text-[#EDE6D6]/70 font-ui leading-relaxed mb-10"
        >
          MeetLoop investigates patterns across transcripts, Notion, and Gmail — quietly
          uncovering the stuck decisions and overloaded teammates before status slips.
        </motion.p>

        {/* CTA Buttons (Exact Inspo Structure) */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto"
        >
          {/* Primary Pill Button */}
          <button
            onClick={onStartAudit}
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-full bg-[#EDE6D6] text-[#15120F] font-ui font-medium text-sm transition-all duration-200 hover:bg-white hover:scale-[1.03] hover:shadow-[0_0_25px_rgba(237,230,214,0.35)] active:scale-[0.98]"
          >
            <span>Run an audit</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          {/* Secondary Translucent Pill Button */}
          <button
            onClick={onQuickDemo}
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-full bg-[#211C17]/90 text-[#EDE6D6] border border-[#EDE6D6]/15 backdrop-blur-md font-ui font-medium text-sm transition-all duration-200 hover:bg-[#211C17] hover:border-[#EDE6D6]/30 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Play className="w-3.5 h-3.5 fill-current text-[#D9A441]" />
            <span>Watch demo run</span>
          </button>
        </motion.div>

        {/* Sub-Footer Microcopy */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.65 }}
          className="mt-6 flex items-center justify-center gap-2 text-[11px] font-mono text-[#EDE6D6]/40"
        >
          <Shield className="w-3 h-3 text-[#4F8F7A]" />
          <span>Governed by Swytchcode Policies • Notion, Gmail, Slack & Google Meet connected</span>
        </motion.div>
      </div>

      {/* 5. Bottom Status Bar & Integration Chips */}
      <motion.footer
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="relative z-20 w-full max-w-6xl flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-[#EDE6D6]/8 text-xs font-mono text-[#EDE6D6]/50"
      >
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4F8F7A]" />
            Swytchcode Policy Engine: FAIL-CLOSED
          </span>
          <span className="hidden md:inline text-[#EDE6D6]/20">•</span>
          <span className="hidden md:inline">Top-N Guardrail: Active (5 Max)</span>
        </div>

        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 text-[#EDE6D6]/70">
            <FileText className="w-3 h-3 text-[#EDE6D6]/40" /> Notion
          </span>
          <span className="flex items-center gap-1 text-[#EDE6D6]/70">
            <Mail className="w-3 h-3 text-[#EDE6D6]/40" /> Gmail
          </span>
          <span className="flex items-center gap-1 text-[#EDE6D6]/70">
            <MessageSquare className="w-3 h-3 text-[#EDE6D6]/40" /> Slack
          </span>
        </div>
      </motion.footer>
    </div>
  );
}
