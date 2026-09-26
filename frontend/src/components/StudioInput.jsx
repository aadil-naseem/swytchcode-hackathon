import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Video, FileText, Sparkles, RefreshCw } from 'lucide-react';

export default function StudioInput({ onBack, onRun, initialMode = 'audit' }) {
  const [mode, setMode] = useState(initialMode); // 'audit' | 'brief'
  const [inputTab, setInputTab] = useState('paste'); // 'paste' | 'gmeet'
  const [textInput, setTextInput] = useState('');
  const [gmeetCode, setGmeetCode] = useState('');
  const [briefTopic, setBriefTopic] = useState('');
  const [fixtures, setFixtures] = useState([]);
  const [loadingFixtures, setLoadingFixtures] = useState(false);

  // Fetch available demo fixtures from backend
  useEffect(() => {
    fetch('/api/fixtures')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.fixtures) {
          setFixtures(data.fixtures);
        }
      })
      .catch((err) => console.log('Fixtures fetch notice:', err));
  }, []);

  const handleLoadSample = (sampleType) => {
    if (sampleType === 'pulseboard') {
      setTextInput(`Title: PulseBoard Weekly Product Sync
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

Meeting ended without a clear launch date for staging.`);
    } else if (sampleType === 'multi_meeting') {
      const combined = fixtures.map((f) => f.content).join('\n\n---\n\n');
      setTextInput(combined || 'Tuesday Engineering Standup...\n\n---\n\nFriday Retrospective...');
    }
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (mode === 'audit') {
      if (inputTab === 'gmeet' && gmeetCode.trim()) {
        onRun({ mode: 'audit', gmeet_meeting_code: gmeetCode.trim() });
      } else {
        onRun({ mode: 'audit', raw_meeting_notes: textInput.trim() || undefined });
      }
    } else {
      onRun({ mode: 'brief', prompt: briefTopic.trim() || 'Pricing Strategy' });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-4xl mx-auto px-4 py-8"
    >
      {/* Top Bar Navigation */}
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-xs font-mono text-[#EDE6D6]/60 hover:text-[#EDE6D6] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Overview
        </button>

        {/* Mode Toggle (Audit vs Brief) */}
        <div className="flex items-center p-1 rounded-full bg-[#211C17] border border-[#EDE6D6]/10 shadow-inner">
          <button
            onClick={() => setMode('audit')}
            className={`px-4 py-1.5 rounded-full text-xs font-ui font-medium transition-all ${
              mode === 'audit'
                ? 'bg-[#B23A2E] text-[#EDE6D6] shadow-[0_0_12px_rgba(178,58,46,0.4)]'
                : 'text-[#EDE6D6]/50 hover:text-[#EDE6D6]'
            }`}
          >
            Audit Mode (Multi-Meeting)
          </button>
          <button
            onClick={() => setMode('brief')}
            className={`px-4 py-1.5 rounded-full text-xs font-ui font-medium transition-all ${
              mode === 'brief'
                ? 'bg-[#B23A2E] text-[#EDE6D6] shadow-[0_0_12px_rgba(178,58,46,0.4)]'
                : 'text-[#EDE6D6]/50 hover:text-[#EDE6D6]'
            }`}
          >
            Brief Mode (Pre-Meeting)
          </button>
        </div>
      </div>

      {/* Main Studio Card */}
      <div className="p-6 md:p-8 rounded-2xl bg-[#211C17]/90 border border-[#EDE6D6]/12 shadow-[0_20px_50px_rgba(0,0,0,0.6)] backdrop-blur-xl">
        {mode === 'audit' ? (
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-xl font-display font-semibold text-[#EDE6D6]">
                  Cross-Meeting Intelligence Audit
                </h2>
                <p className="text-xs text-[#EDE6D6]/60 font-ui mt-1">
                  Feed multi-meeting transcripts or a Google Meet code to uncover hidden circular blockers and workload distribution.
                </p>
              </div>

              {/* Sub-Tabs: Paste Notes vs Google Meet Code */}
              <div className="flex items-center p-1 rounded-lg bg-[#15120F] border border-[#EDE6D6]/8 text-xs font-mono">
                <button
                  onClick={() => setInputTab('paste')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                    inputTab === 'paste' ? 'bg-[#211C17] text-[#D9A441]' : 'text-[#EDE6D6]/40 hover:text-[#EDE6D6]'
                  }`}
                >
                  <FileText className="w-3 h-3" /> Paste Notes
                </button>
                <button
                  onClick={() => setInputTab('gmeet')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-colors ${
                    inputTab === 'gmeet' ? 'bg-[#211C17] text-[#D9A441]' : 'text-[#EDE6D6]/40 hover:text-[#EDE6D6]'
                  }`}
                >
                  <Video className="w-3 h-3" /> Google Meet Code
                </button>
              </div>
            </div>

            {/* Input View: Paste or Google Meet */}
            {inputTab === 'paste' ? (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-[11px] font-mono text-[#EDE6D6]/50">Quick Test Samples:</span>
                  <button
                    type="button"
                    onClick={() => handleLoadSample('pulseboard')}
                    className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-[#15120F] border border-[#EDE6D6]/10 text-[#EDE6D6]/80 hover:border-[#D9A441]/50 hover:text-[#D9A441] transition-all"
                  >
                    ⚡ PulseBoard Sync (Synthetic)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadSample('multi_meeting')}
                    className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-[#15120F] border border-[#EDE6D6]/10 text-[#EDE6D6]/80 hover:border-[#D9A441]/50 hover:text-[#D9A441] transition-all"
                  >
                    📁 4-Meeting Week Sample
                  </button>
                </div>

                <textarea
                  rows={10}
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Paste raw meeting notes or transcripts here (or click a quick test sample above)..."
                  className="w-full p-4 rounded-xl bg-[#15120F] border border-[#EDE6D6]/10 text-[#EDE6D6] font-mono text-xs focus:outline-none focus:border-[#B23A2E] focus:ring-1 focus:ring-[#B23A2E] transition-all resize-y leading-relaxed"
                />
              </div>
            ) : (
              <div className="py-8 px-6 rounded-xl bg-[#15120F] border border-[#EDE6D6]/10 flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-full bg-[#4F8F7A]/15 border border-[#4F8F7A]/30 flex items-center justify-center mb-4 text-[#4F8F7A]">
                  <Video className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-ui font-semibold text-[#EDE6D6] mb-1">
                  Ingest Direct from Google Meet API
                </h3>
                <p className="text-xs text-[#EDE6D6]/50 font-ui max-w-md mb-6">
                  Enter your Google Meet space code (e.g., <code className="text-[#D9A441]">abc-defg-hij</code>). MeetLoop will query conference records and pull speaker dialogue automatically.
                </p>

                <div className="flex w-full max-w-md gap-2">
                  <input
                    type="text"
                    value={gmeetCode}
                    onChange={(e) => setGmeetCode(e.target.value)}
                    placeholder="abc-defg-hij"
                    className="flex-1 px-4 py-2.5 rounded-lg bg-[#211C17] border border-[#EDE6D6]/15 text-[#EDE6D6] font-mono text-sm focus:outline-none focus:border-[#B23A2E]"
                  />
                  <button
                    type="button"
                    onClick={() => setGmeetCode('abc-defg-hij')}
                    className="text-xs font-mono px-3 py-2 rounded-lg bg-[#211C17] border border-[#EDE6D6]/10 text-[#EDE6D6]/60 hover:text-[#EDE6D6]"
                  >
                    Use Sample Code
                  </button>
                </div>
              </div>
            )}

            {/* Action Bar */}
            <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-[#EDE6D6]/8">
              <span className="text-[11px] font-mono text-[#EDE6D6]/40">
                Swytchcode Policy Governance: Output directed to approved Notion, Gmail & Slack targets
              </span>

              <button
                onClick={handleSubmit}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3 rounded-full bg-[#B23A2E] text-[#EDE6D6] font-ui font-medium text-sm transition-all duration-200 hover:bg-[#c94235] hover:scale-[1.02] shadow-[0_0_20px_rgba(178,58,46,0.35)] active:scale-[0.98]"
              >
                <span>Run audit</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          /* Brief Mode Input View */
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-display font-semibold text-[#EDE6D6]">
                Pre-Meeting Context Brief
              </h2>
              <p className="text-xs text-[#EDE6D6]/60 font-ui mt-1">
                Enter an upcoming topic or meeting agenda. MeetLoop searches past Notion pages and Gmail threads to synthesize a 30-second pre-meeting intelligence brief.
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-xs font-mono uppercase tracking-wider text-[#EDE6D6]/50 mb-2">
                Topic or Meeting Title
              </label>
              <input
                type="text"
                value={briefTopic}
                onChange={(e) => setBriefTopic(e.target.value)}
                placeholder="e.g., Pricing Strategy, GPU Infrastructure Migration, Q4 Roadmap"
                className="w-full px-4 py-3 rounded-xl bg-[#15120F] border border-[#EDE6D6]/15 text-[#EDE6D6] font-ui text-sm focus:outline-none focus:border-[#B23A2E] transition-all"
              />
            </div>

            <div className="flex items-center gap-2 mb-8">
              <span className="text-[11px] font-mono text-[#EDE6D6]/40">Sample Topics:</span>
              {['Pricing Strategy', 'Infrastructure Migration to GPU Clusters', 'Tailwind Design System'].map(
                (topic) => (
                  <button
                    key={topic}
                    type="button"
                    onClick={() => setBriefTopic(topic)}
                    className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-[#15120F] border border-[#EDE6D6]/10 text-[#EDE6D6]/70 hover:text-[#D9A441] transition-colors"
                  >
                    {topic}
                  </button>
                )
              )}
            </div>

            <div className="flex items-center justify-end pt-4 border-t border-[#EDE6D6]/8">
              <button
                onClick={handleSubmit}
                className="flex items-center gap-2 px-8 py-3 rounded-full bg-[#B23A2E] text-[#EDE6D6] font-ui font-medium text-sm transition-all duration-200 hover:bg-[#c94235] hover:scale-[1.02] shadow-[0_0_20px_rgba(178,58,46,0.35)]"
              >
                <span>Generate brief</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
