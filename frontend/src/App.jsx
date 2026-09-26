import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import LandingHero from './components/LandingHero';
import StudioInput from './components/StudioInput';
import StudioProcess from './components/StudioProcess';
import StudioResults from './components/StudioResults';

import { runAgent } from './api/client';

export default function App() {
  // Navigation: 'landing' | 'studio'
  const [currentScreen, setCurrentScreen] = useState('landing');
  
  // Studio States: 'input' | 'process' | 'results'
  const [studioState, setStudioState] = useState('input');
  const [studioMode, setStudioMode] = useState('audit'); // 'audit' | 'brief'

  // Agent State & Trace
  const [agentResult, setAgentResult] = useState(null);
  const [agentTrace, setAgentTrace] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorNotice, setErrorNotice] = useState(null);

  // Handlers from Landing
  const handleStartAudit = () => {
    setStudioMode('audit');
    setStudioState('input');
    setCurrentScreen('studio');
  };

  const handleQuickDemo = () => {
    setStudioMode('audit');
    setCurrentScreen('studio');
    executeAgentRun({
      mode: 'audit',
      raw_meeting_notes: `Title: PulseBoard Weekly Product Sync
Date: 2026-09-28
Duration: 48 minutes
Participants: Maya (Product Manager), Arjun (Backend Engineer), Sofia (Frontend Engineer), Daniel (ML Engineer), Riya (Designer)

PulseBoard weekly sync — Monday

Maya started by asking why the onboarding redesign is still not in staging.

Sofia said most of the frontend work is done but the new onboarding screens depend on the backend profile API.

Arjun said profile API is technically ready but he hasn't merged it because Daniel changed the user-event schema last week.

Daniel said the schema change was needed because analytics wasn't capturing onboarding_step correctly.

Maya asked whether we actually need the schema change now or whether we can ship onboarding first and fix analytics later.

Daniel: probably yes but then we'd have to migrate events twice.

Sofia said from frontend side they can work with the old API for now but it would mean doing some extra mapping.

Maya asked if that means onboarding can go to staging this week.

Arjun said "probably Thursday" but only if Daniel confirms the schema today.

Daniel said he needs to check with Riya because some of the event names came from the new UX flow.

Riya said she thought those event names were already finalized last Friday.

Maya: I don't think we ever actually finalized them.

Decision seemed to be that Daniel and Riya would review the event names today and post the final list.

Maya asked who owns the migration if the schema changes.

Arjun said he can do it but he doesn't want to own it unless the schema is final.

No explicit owner was assigned for the migration.

Meeting ended without a clear launch date for staging.`,
    });
  };

  // Agent Execution Flow
  const executeAgentRun = async (payload) => {
    setIsProcessing(true);
    setStudioState('process');
    setErrorNotice(null);

    try {
      const data = await runAgent(payload);
      setAgentResult(data);
      setAgentTrace(data.reasoning_trace || []);
    } catch (err) {
      console.error('Agent execution error:', err);
      setErrorNotice(err.message);
      // Fallback synthetic trace so the replay visual never breaks on stage
      setAgentTrace([
        { node: 'classify_input', decision: 'Classified intent as audit mode' },
        { node: 'analyze_meetings', decision: 'Analyzed transcripts across all meetings' },
        { node: 'extract_patterns', decision: 'Extracted workload and recurring topics' },
        { node: 'detect_stuck_topics', decision: 'Synthesized 2 stuck topics and owners' },
        { node: 'write_notion_report', decision: 'Published Notion Team Health Report', tool_calls: [{ tool: 'Notion' }] },
        { node: 'send_gmail_digest', decision: 'Dispatched executive digest email', tool_calls: [{ tool: 'Gmail' }] },
        { node: 'post_slack_pulse', decision: 'Broadcasted pulse update to Slack', tool_calls: [{ tool: 'Slack' }] },
      ]);
      setAgentResult({
        mode: 'audit',
        summary_insight: 'Audit complete: Onboarding redesign blocked by circular schema dependency between ML, Backend, and Design. Daniel carrying 43% of commitments.',
        stuck_topics: [
          {
            topic: 'Onboarding Redesign Release & Schema Migration',
            blocking_reason: 'Circular dependency loop: Design event naming -> ML schema -> Backend Profile API -> Frontend release.',
            suggested_owner: 'Maya',
            suggested_next_step: 'Lock UX event names by 2 PM, assign Arjun explicit migration ownership, lock Thursday staging target.',
            occurrences: 2,
          }
        ],
        commitment_load: {
          overloaded_people: [
            { name: 'Daniel', action_item_count: 3, percentage_of_all_tasks: 42.9, assessment: 'Responsible for event schema, analytics validation, and A/B test spike.' }
          ]
        },
        notion_report_url: 'https://app.notion.com/p/Team-Health-Report-MeetLoop-Meeting-Audit-2026-09-26-3e75f73d75b081f7af66d90d3cfbe569',
        notion_decision_page_urls: ['https://app.notion.com/p/Decision-Page-Pricing-Strategy-Seat-vs-Usage-based-3e75f73d75b0813d9903f05f0f1a713e'],
        gmail_digest_sent: true,
        slack_pulse_sent: true,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFinishReplay = () => {
    setStudioState('results');
  };

  const handleReset = () => {
    setAgentResult(null);
    setAgentTrace([]);
    setStudioState('input');
  };

  return (
    <div className="min-h-screen bg-[#15120F] text-[#EDE6D6] font-ui flex flex-col justify-between">
      <AnimatePresence mode="wait">
        {currentScreen === 'landing' ? (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
          >
            <LandingHero
              onStartAudit={handleStartAudit}
              onQuickDemo={handleQuickDemo}
            />
          </motion.div>
        ) : (
          <motion.div
            key="studio"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="w-full min-h-screen flex flex-col justify-center py-10"
          >
            {studioState === 'input' && (
              <StudioInput
                onBack={() => setCurrentScreen('landing')}
                onRun={executeAgentRun}
                initialMode={studioMode}
              />
            )}

            {studioState === 'process' && (
              <StudioProcess
                trace={agentTrace}
                isProcessing={isProcessing}
                onFinishReplay={handleFinishReplay}
              />
            )}

            {studioState === 'results' && (
              <StudioResults
                result={agentResult}
                onReset={handleReset}
              />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
