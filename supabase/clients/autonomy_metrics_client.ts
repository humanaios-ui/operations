/**
 * Autonomy Metrics Client — TypeScript SDK for sending events
 *
 * Usage:
 *   const client = new AutonomyMetricsClient(supabaseUrl, anonKey);
 *   await client.sendDecisionEvent({
 *     practiceId: "empirica-autonomy",
 *     title: "Enable safety gate",
 *     dimensions: ["truth", "harm"]
 *   });
 */

type EventType = "decision" | "escalation" | "gate_transition" | "blocker";
type EscalationSeverity = "low" | "medium" | "high" | "critical";
type DecisionStatus = "proposed" | "approved" | "rejected" | "executed" | "escalated";
type Granularity = "hourly" | "daily";

interface EventPayload {
  event_id: string;
  practice_id: string;
  event_type: EventType;
  channel: string;
  payload: Record<string, unknown>;
  dimension?: string;
  metrics?: Record<string, unknown>;
  source_gate?: string;
  tags?: string[];
  created_by?: string;
}

interface MetricsResponse {
  ok: boolean;
  metrics?: Array<{
    metric_date: string;
    metric_hour: number | null;
    practice_id: string | null;
    dimension: string | null;
    events_total: number;
    decisions_proposed: number;
    decisions_approved: number;
    decisions_executed: number;
    escalations_open: number;
    escalations_resolved: number;
    escalation_rate_per_1k: number;
    approval_rate: number;
    execution_rate: number;
  }>;
  escalations?: Array<{
    escalation_id: string;
    timestamp: string;
    practice_id: string;
    reason: string;
    severity: EscalationSeverity;
    status: string;
    escalated_to: string;
    sla_met: boolean;
  }>;
  decision_stats?: {
    total_decisions: number;
    proposed: number;
    approved: number;
    approval_rate: number;
    executed: number;
    execution_rate: number;
  };
  error?: string;
}

interface DecisionEventOptions {
  practiceId: string;
  title: string;
  scope?: string;
  dimensions?: string[];
  confidence?: number;
  sourceGate?: string;
  tags?: string[];
}

interface EscalationEventOptions {
  practiceId: string;
  reason: string;
  severity?: EscalationSeverity;
  escalatedTo?: string;
  sourceDecisionId?: string;
}

export class AutonomyMetricsClient {
  private baseUrl: string;
  private anonKey: string;

  constructor(supabaseUrl: string, anonKey: string) {
    /**
     * Initialize the client
     * @param supabaseUrl Your Supabase project URL (e.g., https://xxx.supabase.co)
     * @param anonKey Your Supabase anon/public key
     */
    this.baseUrl = `${supabaseUrl}/functions/v1/autonomy-metrics`;
    this.anonKey = anonKey;
  }

  private async request<T>(
    endpoint: string,
    method: "GET" | "POST" = "POST",
    body?: Record<string, unknown>
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      "Authorization": `Bearer ${this.anonKey}`,
      "Content-Type": "application/json",
    };

    const options: RequestInit = {
      method,
      headers,
      ...(body && { body: JSON.stringify(body) }),
    };

    const response = await fetch(url, options);

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Send a raw event to the metrics system
   */
  async sendEvent(payload: EventPayload): Promise<{ ok: boolean; event_id: string }> {
    return this.request("/ingest", "POST", payload);
  }

  /**
   * Send a decision event (convenience method)
   */
  async sendDecisionEvent(options: DecisionEventOptions): Promise<{ ok: boolean; event_id: string }> {
    const { practiceId, title, scope = "local", dimensions, confidence = 0.5, sourceGate, tags } = options;

    const eventId = `evt-${Math.random().toString(36).substring(2, 14)}`;

    const payload: EventPayload = {
      event_id: eventId,
      practice_id: practiceId,
      event_type: "decision",
      channel: "decision_proposal",
      payload: {
        proposal_title: title,
        scope,
        confidence,
      },
      source_gate: sourceGate,
      tags: tags || ["decision"],
      created_by: practiceId,
    };

    if (dimensions && dimensions.length > 0) {
      payload.dimension = dimensions[0]; // Primary dimension
    }

    return this.sendEvent(payload);
  }

  /**
   * Send an escalation event
   */
  async sendEscalationEvent(options: EscalationEventOptions): Promise<{ ok: boolean; event_id: string }> {
    const {
      practiceId,
      reason,
      severity = "medium",
      escalatedTo = "mesh-support",
      sourceDecisionId,
    } = options;

    const eventId = `evt-${Math.random().toString(36).substring(2, 14)}`;

    const payload: EventPayload = {
      event_id: eventId,
      practice_id: practiceId,
      event_type: "escalation",
      channel: "escalation_alert",
      payload: {
        reason,
        severity,
        escalated_to: escalatedTo,
        ...(sourceDecisionId && { source_decision_id: sourceDecisionId }),
      },
      tags: ["escalation", severity],
      created_by: practiceId,
    };

    return this.sendEvent(payload);
  }

  /**
   * Get aggregated metrics
   */
  async getMetrics(options?: {
    practiceId?: string;
    dimension?: string;
    startDate?: string;
    endDate?: string;
    granularity?: Granularity;
  }): Promise<MetricsResponse> {
    const params = new URLSearchParams({
      endpoint: "metrics",
      granularity: options?.granularity || "daily",
    });

    if (options?.practiceId) params.append("practice_id", options.practiceId);
    if (options?.dimension) params.append("dimension", options.dimension);
    if (options?.startDate) params.append("start_date", options.startDate);
    if (options?.endDate) params.append("end_date", options.endDate);

    const url = `${this.baseUrl}/metrics?${params.toString()}`;
    const response = await fetch(url, {
      headers: { "Authorization": `Bearer ${this.anonKey}` },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get recent escalations
   */
  async getEscalations(limit: number = 50): Promise<MetricsResponse> {
    const params = new URLSearchParams({
      endpoint: "escalations",
      limit: limit.toString(),
    });

    const url = `${this.baseUrl}/metrics?${params.toString()}`;
    const response = await fetch(url, {
      headers: { "Authorization": `Bearer ${this.anonKey}` },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get decision approval/execution statistics
   */
  async getDecisionStats(practiceId?: string): Promise<MetricsResponse> {
    const params = new URLSearchParams({
      endpoint: "decisions",
    });

    if (practiceId) params.append("practice_id", practiceId);

    const url = `${this.baseUrl}/metrics?${params.toString()}`;
    const response = await fetch(url, {
      headers: { "Authorization": `Bearer ${this.anonKey}` },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}

// ────────────────────────────────────────────────────────────────
// Example usage
// ────────────────────────────────────────────────────────────────

async function example() {
  const supabaseUrl = process.env.SUPABASE_URL || "";
  const supabaseAnonKey = process.env.SUPABASE_ANON_KEY || "";

  if (!supabaseUrl || !supabaseAnonKey) {
    console.error("Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables");
    return;
  }

  const client = new AutonomyMetricsClient(supabaseUrl, supabaseAnonKey);

  try {
    console.log("\n=== Sending Decision Event ===");
    const decisionResult = await client.sendDecisionEvent({
      practiceId: "empirica-autonomy",
      title: "Enable safety gate for Phase 3",
      scope: "system-wide",
      dimensions: ["truth", "harm"],
      confidence: 0.85,
      sourceGate: "autonomy_gate.py",
      tags: ["phase-3", "high-impact"],
    });
    console.log(JSON.stringify(decisionResult, null, 2));

    console.log("\n=== Sending Escalation Event ===");
    const escalationResult = await client.sendEscalationEvent({
      practiceId: "empirica-autonomy",
      reason: "Cross-practice impact detected",
      severity: "high",
      escalatedTo: "mesh-support",
    });
    console.log(JSON.stringify(escalationResult, null, 2));

    console.log("\n=== Fetching Metrics ===");
    const metrics = await client.getMetrics({
      practiceId: "empirica-autonomy",
      granularity: "daily",
    });
    console.log(`Found ${metrics.metrics?.length || 0} metric records`);

    console.log("\n=== Fetching Escalations ===");
    const escalations = await client.getEscalations(5);
    console.log(`Found ${escalations.escalations?.length || 0} escalations`);

    console.log("\n=== Decision Statistics ===");
    const stats = await client.getDecisionStats("empirica-autonomy");
    console.log(JSON.stringify(stats.decision_stats, null, 2));

    console.log("\n✓ All examples completed");
  } catch (error) {
    console.error("Error:", error);
  }
}

// Run examples if executed directly
if (import.meta.main) {
  example();
}
