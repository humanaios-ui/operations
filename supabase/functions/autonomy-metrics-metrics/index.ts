import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const supabase = createClient(supabaseUrl, supabaseServiceKey);

interface MetricsQuery {
  practice_id?: string;
  dimension?: string;
  start_date?: string;
  end_date?: string;
  granularity?: "hourly" | "daily"; // default: daily
}

interface MetricsResponse {
  practice_id: string | null;
  dimension: string | null;
  metric_date: string;
  metric_hour: number | null;
  events_total: number;
  decisions_proposed: number;
  decisions_approved: number;
  decisions_executed: number;
  escalations_open: number;
  escalations_resolved: number;
  escalation_rate_per_1k: number;
  approval_rate: number;
  execution_rate: number;
  escalation_sla_met_count: number;
  escalation_sla_missed_count: number;
  avg_sla_response_seconds: number;
}

/**
 * Get aggregated autonomy metrics for dashboard
 * Supports filtering by practice, dimension, date range
 */
export async function getMetrics(query: MetricsQuery): Promise<MetricsResponse[]> {
  let q = supabase.from("autonomy.metrics").select("*");

  if (query.practice_id) {
    q = q.eq("practice_id", query.practice_id);
  }
  if (query.dimension) {
    q = q.eq("dimension", query.dimension);
  }

  const startDate = query.start_date || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
  const endDate = query.end_date || new Date().toISOString().split("T")[0];

  q = q.gte("metric_date", startDate).lte("metric_date", endDate);

  if (query.granularity === "hourly") {
    q = q.not("metric_hour", "is", null);
  } else {
    q = q.is("metric_hour", null);
  }

  q = q.order("metric_date", { ascending: false });

  const { data, error } = await q;

  if (error) {
    console.error("Error fetching metrics:", error);
    throw error;
  }

  return data || [];
}

/**
 * Get recent escalations with status and SLA info
 */
export async function getEscalations(limit: number = 50) {
  const { data, error } = await supabase
    .from("autonomy.escalations")
    .select("*")
    .order("timestamp", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("Error fetching escalations:", error);
    throw error;
  }

  return data || [];
}

/**
 * Get decision approval/execution rates
 */
export async function getDecisionStats(practice_id?: string) {
  let q = supabase.from("autonomy.decisions").select(
    "status, executed, count(*) as count",
    { count: "exact" }
  );

  if (practice_id) {
    q = q.eq("practice_id", practice_id);
  }

  const { data, error } = await q.group_by("status", "executed");

  if (error) {
    console.error("Error fetching decision stats:", error);
    throw error;
  }

  // Compute rates from raw data
  const stats = data || [];
  const total = stats.reduce((sum, s) => sum + s.count, 0);
  const proposed = stats.filter((s) => s.status === "proposed").reduce((sum, s) => sum + s.count, 0);
  const approved = stats.filter((s) => s.status === "approved").reduce((sum, s) => sum + s.count, 0);
  const executed = stats.filter((s) => s.executed).reduce((sum, s) => sum + s.count, 0);

  return {
    total_decisions: total,
    proposed: proposed,
    approved: approved,
    approval_rate: approved > 0 ? (approved / proposed) * 100 : 0,
    executed: executed,
    execution_rate: executed > 0 ? (executed / approved) * 100 : 0,
  };
}

// ────────────────────────────────────────────────────────────────
// Deno Edge Function Handler
// ────────────────────────────────────────────────────────────────

Deno.serve(async (req: Request) => {
  // CORS
  if (req.method === "OPTIONS") {
    return new Response("OK", {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    });
  }

  if (req.method !== "GET") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const url = new URL(req.url);
    const endpoint = url.searchParams.get("endpoint") || "metrics";

    const response: Record<string, unknown> = {};

    if (endpoint === "metrics") {
      const query: MetricsQuery = {
        practice_id: url.searchParams.get("practice_id") || undefined,
        dimension: url.searchParams.get("dimension") || undefined,
        start_date: url.searchParams.get("start_date") || undefined,
        end_date: url.searchParams.get("end_date") || undefined,
        granularity: (url.searchParams.get("granularity") as any) || "daily",
      };

      response.metrics = await getMetrics(query);
    } else if (endpoint === "escalations") {
      const limit = parseInt(url.searchParams.get("limit") || "50");
      response.escalations = await getEscalations(limit);
    } else if (endpoint === "decisions") {
      const practice_id = url.searchParams.get("practice_id") || undefined;
      response.decision_stats = await getDecisionStats(practice_id);
    } else {
      return new Response(JSON.stringify({ ok: false, error: "Unknown endpoint" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ ok: true, ...response }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err) {
    console.error("Handler error:", err);
    return new Response(
      JSON.stringify({
        ok: false,
        error: "Failed to fetch metrics",
        detail: String(err),
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
});
