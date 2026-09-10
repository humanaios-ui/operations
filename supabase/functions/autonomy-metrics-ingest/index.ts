import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const supabase = createClient(supabaseUrl, supabaseServiceKey);

interface AutonomyEvent {
  event_id: string;
  timestamp?: string;
  practice_id: string;
  event_type: "decision" | "escalation" | "gate_transition" | "blocker";
  dimension?: string;
  channel: string;
  payload: Record<string, unknown>;
  metrics?: Record<string, unknown>;
  source_gate?: string;
  parent_event_id?: string;
  tags?: string[];
  created_by?: string;
}

export async function ingestEvent(event: AutonomyEvent) {
  const {
    event_id,
    timestamp = new Date().toISOString(),
    practice_id,
    event_type,
    dimension,
    channel,
    payload,
    metrics = {},
    source_gate,
    parent_event_id,
    tags = [],
    created_by,
  } = event;

  try {
    const { error } = await supabase.from("autonomy.events").insert({
      event_id,
      timestamp,
      practice_id,
      event_type,
      dimension,
      channel,
      payload,
      metrics,
      source_gate,
      parent_event_id,
      tags,
      created_by,
    });

    if (error) {
      console.error("Error inserting event:", error);
      return { ok: false, error: error.message };
    }

    return { ok: true, event_id };
  } catch (err) {
    console.error("Unexpected error:", err);
    return { ok: false, error: String(err) };
  }
}

// Deno Edge Function handler
Deno.serve(async (req: Request) => {
  // Handle CORS
  if (req.method === "OPTIONS") {
    return new Response("OK", {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    });
  }

  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const body: AutonomyEvent = await req.json();

    // Validate required fields
    if (!body.event_id || !body.practice_id || !body.event_type || !body.channel) {
      return new Response(
        JSON.stringify({
          ok: false,
          error: "Missing required fields: event_id, practice_id, event_type, channel",
        }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const result = await ingestEvent(body);

    if (result.ok) {
      return new Response(JSON.stringify(result), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      });
    } else {
      return new Response(JSON.stringify(result), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }
  } catch (err) {
    console.error("Handler error:", err);
    return new Response(
      JSON.stringify({
        ok: false,
        error: "Failed to process request",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});
