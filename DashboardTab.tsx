// === ADD / REPLACE in DashboardTab.tsx ===

import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL!,
  import.meta.env.VITE_SUPABASE_ANON_KEY!
);

export function DashboardTab({ ... }) {
  const [liveState, setLiveState] = useState({
    pipeline: 'YELLOW',
    openCount: 23,
    runway: '~50 days',
    revenue: 0
  });

  useEffect(() => {
    const fetchLive = async () => {
      const [{ data: op }, { data: z3 }] = await Promise.all([
        supabase.from('operational_state_live').select('*').single(),
        supabase.from('zone3_open_live').select('*').single()
      ]);

      if (op) {
        setLiveState({
          pipeline: op.pipeline_color || 'YELLOW',
          openCount: z3?.open_count || 23,
          runway: `${op.runway_days || 50} days`,
          revenue: Number(op.revenue_usd) || 0
        });
      }
    };

    fetchLive();
    const interval = setInterval(fetchLive, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // Use liveState in your tiles instead of hardcoded values
  return (
    <div>
      {/* Example updated KPI tile */}
      <div className="stat">
        <div className="stat-label">PIPELINE</div>
        <div style={{ color: liveState.pipeline === 'YELLOW' ? '#D4A04A' : liveState.pipeline === 'RED' ? '#D97D70' : '#87b68b' }}>
          {liveState.pipeline}
        </div>
      </div>

      {/* Critical items from live Z3 */}
      <div>CRITICAL-ESCALATED ({liveState.openCount})</div>
      {/* ... rest of your component */}
    </div>
  );
}