import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import confetti from 'canvas-confetti';
import {
  FileText,
  Mail,
  MessageSquare,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  Shield,
  RotateCcw,
  CheckCircle,
  UserCheck,
  Zap,
} from 'lucide-react';
import DecryptedText from './reactbits/DecryptedText';
import SpotlightCard from './reactbits/SpotlightCard';

export default function StudioResults({ result = {}, onReset }) {
  const mode = result.mode || 'audit';
  const isAudit = mode === 'audit';
  const stuckTopics = result.stuck_topics || [];
  const commitmentLoad = result.commitment_load || {};
  const overloaded = commitmentLoad.overloaded_people || [];
  const reportUrl = result.notion_report_url;
  const decisionUrls = result.notion_decision_page_urls || [];
  const gmailSent = result.gmail_digest_sent;
  const slackSent = result.slack_pulse_sent;

  // Trigger subtle confetti on verdict reveal
  useEffect(() => {
    confetti({
      particleCount: 35,
      spread: 60,
      origin: { y: 0.8 },
      colors: ['#B23A2E', '#D9A441', '#EDE6D6', '#4F8F7A'],
      disableForReducedMotion: true,
    });
  }, []);

  const headlineVerdict = isAudit
    ? result.summary_insight ||
      `${stuckTopics.length} stuck topic(s) detected across meetings. Action items disproportionately held by ${overloaded[0]?.name || 'engineering'}.`
    : result.summary_insight || 'Pre-meeting brief synthesized from Notion and Gmail records.';

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="w-full max-w-5xl mx-auto px-4 py-8"
    >
      {/* Top Header / Actions */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-[#EDE6D6]/10">
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#4F8F7A]" />
          <h2 className="font-mono text-xs uppercase tracking-widest text-[#EDE6D6]/60">
            Case Verdict & Intelligence Deliverables
          </h2>
        </div>

        <button
          onClick={onReset}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-[#211C17] border border-[#EDE6D6]/15 text-xs font-mono text-[#EDE6D6] hover:bg-[#B23A2E] hover:border-[#B23A2E] transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>New Investigation</span>
        </button>
      </div>

      {/* 1. THE VERDICT (Huge DecryptedText Reveal) */}
      <div className="p-8 rounded-2xl bg-[#211C17]/90 border border-[#B23A2E]/40 shadow-[0_20px_50px_rgba(178,58,46,0.15)] mb-8">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#D9A441] mb-3">
          <Zap className="w-3.5 h-3.5 text-[#D9A441]" />
          <span>Primary Cross-Meeting Finding</span>
        </div>

        <div className="text-xl sm:text-2xl md:text-3xl font-display font-semibold text-[#EDE6D6] leading-snug">
          <DecryptedText
            text={headlineVerdict}
            speed={25}
            maxIterations={12}
            className="text-[#EDE6D6]"
            encryptedClassName="text-[#B23A2E]"
          />
        </div>
      </div>

      {isAudit ? (
        <div className="space-y-8">
          {/* 2. OVERLOADED TEAM MEMBERS (Human Cost) */}
          {overloaded.length > 0 && (
            <div className="p-5 rounded-xl bg-[#B23A2E]/10 border border-[#B23A2E]/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-[#B23A2E] mt-0.5" />
                <div>
                  <h3 className="text-sm font-ui font-semibold text-[#EDE6D6]">
                    Workload Bottleneck Alert: {overloaded[0].name}
                  </h3>
                  <p className="text-xs text-[#EDE6D6]/70 font-ui mt-0.5">
                    Assigned {overloaded[0].action_item_count} tasks ({overloaded[0].percentage_of_all_tasks}% of entire team commitments). {overloaded[0].assessment}
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-mono text-[#B23A2E] px-3 py-1 rounded-full bg-[#B23A2E]/20 whitespace-nowrap">
                High Bottleneck Risk
              </span>
            </div>
          )}

          {/* 3. STUCK TOPICS BOARD (Pinned Evidence Cards) */}
          <div>
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#EDE6D6]/50 mb-4 flex items-center gap-2">
              <span>Unresolved Recurring Issues ({stuckTopics.length})</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {stuckTopics.map((topic, idx) => (
                <SpotlightCard
                  key={idx}
                  className="p-5 flex flex-col justify-between"
                  spotlightColor="rgba(178, 58, 46, 0.25)"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h4 className="text-sm font-ui font-semibold text-[#EDE6D6]">
                        {topic.topic}
                      </h4>
                      <span className="text-[10px] font-mono text-[#D9A441] bg-[#D9A441]/10 px-2 py-0.5 rounded-md border border-[#D9A441]/20">
                        {topic.occurrences || 2} Meetings
                      </span>
                    </div>

                    <div className="space-y-2.5 my-3 text-xs">
                      <div>
                        <span className="text-[#EDE6D6]/40 font-mono text-[10px] uppercase">Root Blocker:</span>
                        <p className="text-[#EDE6D6]/80 font-ui mt-0.5 leading-relaxed">
                          {topic.blocking_reason}
                        </p>
                      </div>

                      <div>
                        <span className="text-[#EDE6D6]/40 font-mono text-[10px] uppercase">Recommended Action:</span>
                        <p className="text-[#4F8F7A] font-ui font-medium mt-0.5">
                          {topic.suggested_next_step}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-[#EDE6D6]/8 flex items-center justify-between text-xs">
                    <span className="font-mono text-[11px] text-[#EDE6D6]/60 flex items-center gap-1">
                      <UserCheck className="w-3.5 h-3.5 text-[#D9A441]" /> Driver: @{topic.suggested_owner}
                    </span>

                    {idx < decisionUrls.length && (
                      <a
                        href={decisionUrls[idx]}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-[11px] font-mono text-[#EDE6D6] hover:text-[#D9A441] transition-colors"
                      >
                        <span>Decision Page</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </SpotlightCard>
              ))}
            </div>
          </div>

          {/* 4. REAL ARTIFACT CONFIRMATION CHIPS (Evidence Exhibits) */}
          <div className="p-6 rounded-2xl bg-[#15120F] border border-[#EDE6D6]/10">
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#EDE6D6]/50 mb-4">
              Generated Integrations & Evidence Exhibits
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Notion Health Report */}
              <div className="p-4 rounded-xl bg-[#211C17] border border-[#EDE6D6]/10 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 text-xs font-mono text-[#EDE6D6] mb-1">
                    <FileText className="w-4 h-4 text-[#EDE6D6]/70" />
                    <span>Notion Health Report</span>
                  </div>
                  <p className="text-[11px] text-[#EDE6D6]/50">5-Section Cross-Meeting Audit</p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#EDE6D6]/8">
                  {reportUrl ? (
                    <a
                      href={reportUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-mono text-[#4F8F7A] hover:underline"
                    >
                      <span>Open in Notion</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-xs font-mono text-[#4F8F7A]">Created</span>
                  )}
                </div>
              </div>

              {/* Gmail Digest */}
              <div className="p-4 rounded-xl bg-[#211C17] border border-[#EDE6D6]/10 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 text-xs font-mono text-[#EDE6D6] mb-1">
                    <Mail className="w-4 h-4 text-[#EDE6D6]/70" />
                    <span>Gmail Executive Digest</span>
                  </div>
                  <p className="text-[11px] text-[#EDE6D6]/50">Delivered to Manager Inbox</p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#EDE6D6]/8 flex items-center gap-1.5 text-xs font-mono text-[#4F8F7A]">
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>{gmailSent ? 'Dispatched (200 OK)' : 'Simulated (Dry-Run)'}</span>
                </div>
              </div>

              {/* Slack Pulse */}
              <div className="p-4 rounded-xl bg-[#211C17] border border-[#EDE6D6]/10 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 text-xs font-mono text-[#EDE6D6] mb-1">
                    <MessageSquare className="w-4 h-4 text-[#EDE6D6]/70" />
                    <span>Slack Weekly Pulse</span>
                  </div>
                  <p className="text-[11px] text-[#EDE6D6]/50">Broadcasted to Team Channel</p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#EDE6D6]/8 flex items-center gap-1.5 text-xs font-mono text-[#4F8F7A]">
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>{slackSent ? 'Posted to Channel' : 'Simulated (Dry-Run)'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Brief Mode Results View */
        <div className="p-6 rounded-2xl bg-[#15120F] border border-[#EDE6D6]/10 space-y-6">
          <div>
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#D9A441] mb-2">
              Pre-Meeting Intelligence Synthesis
            </h3>
            <p className="text-sm text-[#EDE6D6] font-ui leading-relaxed">
              {result.brief_output?.executive_summary || 'Context brief ready for your sync.'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-[#211C17] border border-[#EDE6D6]/10">
              <h4 className="text-xs font-mono text-[#4F8F7A] uppercase mb-2">Past Decisions</h4>
              <p className="text-xs text-[#EDE6D6]/80 font-ui leading-relaxed">
                {result.brief_output?.past_decisions || 'No prior conflicts recorded.'}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#211C17] border border-[#EDE6D6]/10">
              <h4 className="text-xs font-mono text-[#B23A2E] uppercase mb-2">Open Blockers</h4>
              <p className="text-xs text-[#EDE6D6]/80 font-ui leading-relaxed">
                {result.brief_output?.open_blockers || 'Pending agenda alignment.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
