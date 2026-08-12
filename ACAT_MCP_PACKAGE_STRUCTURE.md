# ACAT MCP Package Structure

**Purpose:** Create MCP endpoints wrapping the existing ACAT API for real-time orchestration with RentAHuman  
**Base API:** `operations/acat/api` (Python FastAPI - already has assessment endpoints)  
**MCP Framework:** FastMCP (TypeScript/Node.js)  
**Location:** Create at `operations/acat/mcp/` (extends existing minimal server)

---

## Package Structure

```
acat-mcp/
├── src/
│   ├── server.ts                    # Main MCP server (FastMCP instance)
│   ├── tools/
│   │   ├── assess.ts                # assess_worker tool
│   │   ├── predict.ts               # predict_performance tool
│   │   ├── score.ts                 # score_match tool
│   │   ├── learn.ts                 # learn_from_feedback tool
│   │   └── index.ts                 # Tool exports
│   ├── services/
│   │   ├── acat-api-client.ts       # HTTP client to existing ACAT API
│   │   ├── calibration.ts           # Model weight management + learning
│   │   ├── persistence.ts           # Save/load calibration to GitHub + DB
│   │   └── index.ts                 # Service exports
│   ├── models/
│   │   ├── types.ts                 # TypeScript interfaces
│   │   ├── schemas.ts               # Zod schemas for validation
│   │   └── index.ts                 # Model exports
│   ├── utils/
│   │   ├── logger.ts                # Structured logging
│   │   ├── errors.ts                # Error handling
│   │   └── config.ts                # Environment config
│   └── index.ts                     # Main entry point
├── tests/
│   ├── tools/
│   │   ├── assess.test.ts
│   │   ├── predict.test.ts
│   │   ├── score.test.ts
│   │   └── learn.test.ts
│   └── services/
│       ├── acat-api-client.test.ts
│       └── calibration.test.ts
├── .env.example                     # Environment variables template
├── package.json                     # NPM configuration
├── tsconfig.json                    # TypeScript config
├── README.md                        # Setup & usage guide
└── docker-compose.yml               # Optional: run ACAT API + MCP locally
```

---

## Core Files

### 1. `src/server.ts` — MCP Server Instance

```typescript
import Anthropic from "@anthropic-ai/sdk";
import { FastMCP } from "fastmcp";
import {
  assessWorkerTool,
  predictPerformanceTool,
  scoreMatchTool,
  learnFromFeedbackTool,
} from "./tools";

const mcp = new FastMCP({
  name: "acat-mcp",
  version: "1.0.0",
  description:
    "ACAT behavioral assessment + real-time learning for fair task matching",
});

// Register tools
mcp.addTool(assessWorkerTool);
mcp.addTool(predictPerformanceTool);
mcp.addTool(scoreMatchTool);
mcp.addTool(learnFromFeedbackTool);

// Start server
mcp.start();
export default mcp;
```

**Startup:**
```bash
npm start
# Listens on stdio (for Claude) or HTTP (for standalone)
# Exposes 4 main tools
```

---

### 2. `src/tools/assess.ts` — Assess Worker Tool

```typescript
import { Tool } from "fastmcp";
import { ACATApiClient } from "../services/acat-api-client";
import { AssessmentRequest, AssessmentResponse } from "../models/types";

export const assessWorkerTool: Tool = {
  name: "assess_worker",
  description:
    "Run ACAT assessment on a worker for a specific task. Returns behavioral scores (Consistency, Truthfulness, Sycophancy, Harm) + reasoning.",
  inputSchema: {
    type: "object",
    properties: {
      worker_profile: {
        type: "object",
        description:
          "Worker info from RAH (id, skills, hourly_rate, rating, bio, prior_jobs)",
        properties: {
          id: { type: "string", description: "Worker ID from RAH" },
          name: { type: "string" },
          skills: { type: "array", items: { type: "string" } },
          hourly_rate: { type: "number" },
          rating: { type: "number", description: "1-5 stars" },
          prior_jobs: { type: "number" },
          bio: { type: "string" },
        },
        required: ["id", "name", "skills"],
      },
      task_requirements: {
        type: "object",
        description:
          "What this task needs from the worker (weighted importance 0-1)",
        properties: {
          consistency_needed: {
            type: "number",
            description: "Weight for consistency (0-1)",
          },
          truthfulness_needed: {
            type: "number",
            description: "Weight for truthfulness (0-1)",
          },
          sycophancy_tolerance: {
            type: "number",
            description: "Tolerance for sycophancy (lower = independent thinking needed)",
          },
          harm_tolerance: {
            type: "number",
            description: "Tolerance for harm risk (lower = ethical priority)",
          },
          task_type: {
            type: "string",
            enum: ["research", "writing", "analysis", "validation", "design"],
          },
        },
        required: ["task_type"],
      },
      historical_data: {
        type: "array",
        description: "Prior tasks this worker completed (optional, for learning)",
        items: {
          type: "object",
          properties: {
            task_id: { type: "string" },
            task_type: { type: "string" },
            quality_rating: { type: "number" },
            completion_time_days: { type: "number" },
            satisfaction: { type: "number" },
          },
        },
      },
    },
    required: ["worker_profile", "task_requirements"],
  },

  execute: async (input: AssessmentRequest): Promise<AssessmentResponse> => {
    const client = new ACATApiClient();

    // Call existing ACAT API (POST /api/v1/acat/assess)
    const assessment = await client.assessWorker(input.worker_profile);

    // Score the assessment against task requirements
    const score = scoreAssessment(assessment, input.task_requirements);

    return {
      worker_id: input.worker_profile.id,
      acat_scores: {
        consistency: assessment.consistency,
        truthfulness: assessment.truthfulness,
        sycophancy: assessment.sycophancy,
        harm: assessment.harm,
      },
      match_score: score.match_score, // 0-1
      reasoning: score.reasoning,
      confidence: score.confidence,
      predicted_quality: score.predicted_quality, // 1-5
      predicted_completion_days: score.predicted_completion_days,
    };
  },
};

function scoreAssessment(
  assessment: ACATScores,
  requirements: TaskRequirements
): ScoringResult {
  // Weighted scoring logic
  const consistency_component = assessment.consistency * requirements.consistency_needed;
  const truthfulness_component = assessment.truthfulness * requirements.truthfulness_needed;
  const sycophancy_penalty = Math.max(0, assessment.sycophancy - requirements.sycophancy_tolerance);
  const harm_penalty = Math.max(0, assessment.harm - requirements.harm_tolerance);

  const match_score =
    (consistency_component +
      truthfulness_component -
      sycophancy_penalty * 0.3 -
      harm_penalty * 0.2) /
    (requirements.consistency_needed + requirements.truthfulness_needed);

  return {
    match_score: Math.min(1, Math.max(0, match_score)),
    reasoning: `Scored ${match_score.toFixed(2)} based on task requirements...`,
    confidence: calculateConfidence(assessment),
    predicted_quality: predictQuality(assessment, requirements),
    predicted_completion_days: predictCompletionTime(assessment),
  };
}
```

**Usage (in orchestration):**
```typescript
// Pseudo-code
const assessment = await mcp.call("assess_worker", {
  worker_profile: { id: "rah_123", name: "Dr. Chen", skills: ["research"] },
  task_requirements: {
    task_type: "research",
    consistency_needed: 0.9,
    truthfulness_needed: 0.95,
  },
});
// Returns: {match_score: 0.87, reasoning: "High truthfulness...", predicted_quality: 4.5}
```

---

### 3. `src/tools/score.ts` — Score Match Tool

```typescript
import { Tool } from "fastmcp";

export const scoreMatchTool: Tool = {
  name: "score_match",
  description:
    "Compare multiple worker assessments and return ranked list for a task. Returns top N workers sorted by fit.",
  inputSchema: {
    type: "object",
    properties: {
      task_id: { type: "string" },
      task_requirements: { type: "object" },
      worker_assessments: {
        type: "array",
        description: "Output from assess_worker for multiple workers",
        items: { type: "object" },
      },
      top_n: {
        type: "number",
        description: "How many top matches to return",
        default: 3,
      },
    },
    required: ["task_requirements", "worker_assessments"],
  },

  execute: async (input) => {
    // Sort assessments by match_score (descending)
    const ranked = input.worker_assessments
      .sort((a, b) => b.match_score - a.match_score)
      .slice(0, input.top_n);

    return {
      task_id: input.task_id,
      ranked_workers: ranked.map((w, idx) => ({
        rank: idx + 1,
        worker_id: w.worker_id,
        match_score: w.match_score,
        reasoning: w.reasoning,
        invitation_message: generateInvitation(w, idx + 1),
      })),
    };
  },
};

function generateInvitation(assessment, rank) {
  return `We matched you to this task because: ${assessment.reasoning}. 
    You're our #${rank} choice. Your background + experience make you ideal for this work.`;
}
```

---

### 4. `src/tools/learn.ts` — Learn from Feedback Tool

```typescript
import { Tool } from "fastmcp";
import { CalibrationService } from "../services/calibration";

export const learnFromFeedbackTool: Tool = {
  name: "learn_from_feedback",
  description:
    "Feed task outcome back into ACAT. Recalibrates model weights based on prediction accuracy.",
  inputSchema: {
    type: "object",
    properties: {
      worker_id: { type: "string" },
      task_id: { type: "string" },
      task_type: { type: "string" },
      acat_prediction: {
        type: "object",
        properties: {
          match_score: { type: "number" },
          predicted_quality: { type: "number" },
          predicted_completion_days: { type: "number" },
        },
      },
      actual_outcome: {
        type: "object",
        description: "Actual results from task completion",
        properties: {
          quality_rating: { type: "number", description: "1-5 employer rating" },
          completion_time_days: { type: "number" },
          satisfaction: { type: "number", description: "1-5 worker satisfaction" },
          completed: { type: "boolean" },
          feedback: { type: "string" },
        },
        required: ["quality_rating", "completed"],
      },
    },
    required: ["worker_id", "task_id", "acat_prediction", "actual_outcome"],
  },

  execute: async (input) => {
    const calibration = new CalibrationService();

    // Calculate prediction error
    const quality_error = Math.abs(
      input.acat_prediction.predicted_quality - input.actual_outcome.quality_rating
    );
    const time_error = Math.abs(
      input.acat_prediction.predicted_completion_days -
        input.actual_outcome.completion_time_days
    );

    // Update model weights
    const old_weights = calibration.getWeights(input.task_type);
    const new_weights = calibration.recalibrate({
      task_type: input.task_type,
      quality_error,
      time_error,
      old_weights,
    });

    // Store worker-specific patterns
    await calibration.logWorkerOutcome({
      worker_id: input.worker_id,
      task_type: input.task_type,
      prediction_accuracy: 1 - quality_error / 5, // 0-1
      actual_quality: input.actual_outcome.quality_rating,
      worker_satisfaction: input.actual_outcome.satisfaction,
    });

    // Persist to GitHub + DB
    await calibration.persist();

    return {
      calibration_updated: true,
      quality_error,
      time_error,
      new_weights,
      accuracy_improvement: calculateImprovement(old_weights, new_weights),
      log_message: `ACAT recalibrated for ${input.task_type} tasks. 
                     Quality prediction error: ${quality_error.toFixed(2)}.
                     New weights: ${JSON.stringify(new_weights)}`,
    };
  },
};

function calculateImprovement(old_weights, new_weights) {
  // Calculate how much accuracy improved
  return "...";
}
```

---

### 5. `src/services/acat-api-client.ts` — API Client

```typescript
import axios from "axios";
import { Logger } from "../utils/logger";

export class ACATApiClient {
  private baseUrl: string;
  private logger: Logger;

  constructor(baseUrl = process.env.ACAT_API_URL || "http://localhost:8000") {
    this.baseUrl = baseUrl;
    this.logger = new Logger("ACATApiClient");
  }

  async assessWorker(workerProfile: WorkerProfile): Promise<ACATScores> {
    try {
      // Call existing ACAT API: POST /api/v1/acat/assess
      const response = await axios.post(
        `${this.baseUrl}/api/v1/acat/assess`,
        {
          worker_id: workerProfile.id,
          worker_bio: workerProfile.bio,
          skills: workerProfile.skills,
          prior_jobs: workerProfile.prior_jobs,
          rating: workerProfile.rating,
        },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${process.env.ACAT_API_KEY}`,
          },
        }
      );

      this.logger.info(`Assessed worker ${workerProfile.id}`, response.data);
      return response.data;
    } catch (error) {
      this.logger.error(`Failed to assess worker ${workerProfile.id}`, error);
      throw error;
    }
  }

  async intakePhase1(workerData: any): Promise<any> {
    // Call POST /api/v1/acat/intake/phase1 if needed
    const response = await axios.post(
      `${this.baseUrl}/api/v1/acat/intake/phase1`,
      workerData
    );
    return response.data;
  }

  async intakePhase3(workerData: any): Promise<any> {
    // Call POST /api/v1/acat/intake/phase3 if needed
    const response = await axios.post(
      `${this.baseUrl}/api/v1/acat/intake/phase3`,
      workerData
    );
    return response.data;
  }
}
```

---

### 6. `src/services/calibration.ts` — Learning + Weight Management

```typescript
import { Logger } from "../utils/logger";
import { GitHubPersistence } from "./persistence";
import { Database } from "../database";

export class CalibrationService {
  private logger: Logger;
  private github: GitHubPersistence;
  private db: Database;

  // Current model weights (default values)
  private weights = {
    research: {
      consistency: 0.25,
      truthfulness: 0.30,
      sycophancy: 0.20, // penalty weight
      harm: 0.15, // penalty weight
      task_type_weight: 1.0,
    },
    writing: {
      consistency: 0.20,
      truthfulness: 0.25,
      sycophancy: 0.15,
      harm: 0.20,
      task_type_weight: 1.0,
    },
    analysis: {
      consistency: 0.28,
      truthfulness: 0.32,
      sycophancy: 0.18,
      harm: 0.12,
      task_type_weight: 1.0,
    },
  };

  // Worker-specific multipliers (learned over time)
  private workerPatterns = new Map();

  constructor() {
    this.logger = new Logger("CalibrationService");
    this.github = new GitHubPersistence();
    this.db = new Database();
  }

  getWeights(taskType: string): TaskWeights {
    return this.weights[taskType] || this.weights.research;
  }

  recalibrate(input: {
    task_type: string;
    quality_error: number;
    time_error: number;
    old_weights: TaskWeights;
  }): TaskWeights {
    const { task_type, quality_error, old_weights } = input;

    // If prediction was very accurate, no change needed
    if (quality_error < 0.3) {
      this.logger.info(`Prediction very accurate. No recalibration needed.`);
      return old_weights;
    }

    // If under-predicted (error > 0.5), boost the weights that contributed
    if (quality_error > 0.5) {
      const adjustedWeights = {
        ...old_weights,
        consistency: old_weights.consistency + 0.02,
        truthfulness: old_weights.truthfulness + 0.01,
      };

      // Normalize to sum to 1
      return this.normalizeWeights(adjustedWeights);
    }

    // If over-predicted, reduce weight
    const adjustedWeights = {
      ...old_weights,
      consistency: Math.max(0.1, old_weights.consistency - 0.01),
      truthfulness: Math.max(0.1, old_weights.truthfulness - 0.01),
    };

    return this.normalizeWeights(adjustedWeights);
  }

  async logWorkerOutcome(data: {
    worker_id: string;
    task_type: string;
    prediction_accuracy: number;
    actual_quality: number;
    worker_satisfaction: number;
  }): Promise<void> {
    // Store in database for analytics
    await this.db.logOutcome(data);

    // Update worker-specific pattern
    const pattern = this.workerPatterns.get(data.worker_id) || {
      task_type_strengths: {},
      avg_quality: 4.0,
      total_completed: 0,
    };

    pattern.task_type_strengths[data.task_type] =
      (pattern.task_type_strengths[data.task_type] || 0) + data.actual_quality;
    pattern.avg_quality = (pattern.avg_quality + data.actual_quality) / 2;
    pattern.total_completed += 1;

    this.workerPatterns.set(data.worker_id, pattern);

    this.logger.info(`Logged outcome for worker ${data.worker_id}`, pattern);
  }

  async persist(): Promise<void> {
    // Save to GitHub (transparent audit log)
    await this.github.saveCalibration({
      timestamp: new Date().toISOString(),
      weights: this.weights,
      worker_patterns: Array.from(this.workerPatterns.entries()),
    });

    // Save to database (for runtime queries)
    await this.db.saveCalibration(this.weights);

    this.logger.info("Calibration persisted to GitHub + Database");
  }

  private normalizeWeights(weights: any): TaskWeights {
    // Ensure weights sum to ~1.0
    const sum = Object.values(weights).reduce((a, b) => a + b, 0);
    return Object.fromEntries(
      Object.entries(weights).map(([k, v]) => [k, (v as number) / sum])
    );
  }
}
```

---

### 7. `src/models/types.ts` — TypeScript Types

```typescript
export interface WorkerProfile {
  id: string;
  name: string;
  skills: string[];
  hourly_rate: number;
  rating: number; // 1-5
  prior_jobs: number;
  bio?: string;
}

export interface TaskRequirements {
  task_type: "research" | "writing" | "analysis" | "validation" | "design";
  consistency_needed?: number;
  truthfulness_needed?: number;
  sycophancy_tolerance?: number;
  harm_tolerance?: number;
}

export interface ACATScores {
  consistency: number; // 0-1
  truthfulness: number; // 0-1
  sycophancy: number; // 0-1 (higher = bad)
  harm: number; // 0-1 (higher = bad)
}

export interface AssessmentResponse {
  worker_id: string;
  acat_scores: ACATScores;
  match_score: number; // 0-1, how well worker fits task
  reasoning: string;
  confidence: number; // 0-1, confidence in prediction
  predicted_quality: number; // 1-5
  predicted_completion_days: number;
}

export interface TaskOutcome {
  worker_id: string;
  task_id: string;
  task_type: string;
  quality_rating: number; // 1-5 employer rating
  completion_time_days: number;
  satisfaction: number; // 1-5 worker satisfaction
  completed: boolean;
  feedback?: string;
}

export interface CalibrationDelta {
  consistency_weight: number;
  truthfulness_weight: number;
  sycophancy_weight: number;
  harm_weight: number;
}

export interface TaskWeights {
  consistency: number;
  truthfulness: number;
  sycophancy: number;
  harm: number;
  task_type_weight: number;
}
```

---

### 8. `package.json`

```json
{
  "name": "acat-mcp",
  "version": "1.0.0",
  "description": "ACAT behavioral assessment MCP for fair task matching + real-time calibration",
  "main": "dist/server.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js",
    "dev": "ts-node src/server.ts",
    "test": "jest",
    "test:watch": "jest --watch",
    "lint": "eslint src/**/*.ts"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "^0.24.0",
    "fastmcp": "^1.0.0",
    "axios": "^1.7.0",
    "dotenv": "^16.4.0",
    "pino": "^8.17.0",
    "zod": "^3.22.0",
    "pg": "^8.11.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "@types/jest": "^29.5.0",
    "typescript": "^5.3.0",
    "ts-node": "^10.9.0",
    "jest": "^29.7.0",
    "ts-jest": "^29.1.0",
    "eslint": "^8.55.0"
  }
}
```

---

### 9. `.env.example`

```bash
# ACAT API Configuration
ACAT_API_URL=http://localhost:8000
ACAT_API_KEY=your_api_key_here

# RentAHuman API (for orchestration context)
RAH_API_KEY=rah_75ccef6056b836f84c045982d87b4ef0
RAH_API_URL=https://rentahuman.ai/api/v1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/acat_calibration

# GitHub (for transparency log)
GITHUB_TOKEN=ghp_your_token
GITHUB_REPO=humanaios-ui/operations
GITHUB_CALIBRATION_PATH=acat/mcp/calibration-log

# Logging
LOG_LEVEL=info
```

---

## Integration with Orchestration

### How `acat-mcp` Fits Into Phase 1

**Week 1-2: Setup**
1. Install & configure `acat-mcp`
2. Connect to existing ACAT API
3. Initialize calibration (load defaults)
4. Compose with RAH MCP

**Week 3-4: Real-Time Orchestration**
```typescript
// orchestration.ts (pseudo-code)
import { ACATMcp } from "acat-mcp";
import { RAHMcp } from "rentahuman-mcp";

// 1. RAH discovers workers
const workers = await rah.search_humans({
  skills: ["research"],
  rating_min: 4.0,
});

// 2. ACAT assesses each
const assessments = await Promise.all(
  workers.map((w) => acat.assess_worker({
    worker_profile: w,
    task_requirements: taskRequirements,
  }))
);

// 3. ACAT scores & ranks
const ranked = await acat.score_match({
  task_requirements: taskRequirements,
  worker_assessments: assessments,
  top_n: 3,
});

// 4. RAH invites
await rah.invite_workers({
  bounty_id: bountyId,
  worker_ids: ranked.map((r) => r.worker_id),
  personal_message: ranked.map((r) => r.invitation_message),
});

// 5. (Later) ACAT learns
const outcome = await rah.get_submission(bountyId);
await acat.learn_from_feedback({
  worker_id: outcome.worker_id,
  task_id: bountyId,
  acat_prediction: assessments[0], // The matched worker
  actual_outcome: outcome,
});
```

---

## Deployment

### Option A: Docker Compose (Local)

```yaml
version: "3.9"
services:
  acat-api:
    image: humanaios/acat-api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/acat

  acat-mcp:
    build: ./acat-mcp
    depends_on:
      - acat-api
    environment:
      - ACAT_API_URL=http://acat-api:8000
      - ACAT_API_KEY=${ACAT_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/acat_calibration
    ports:
      - "3000:3000"

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=acat_calibration
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Option B: Cloud Deployment (Week 2+)

- Host ACAT MCP on Railway / Render / Heroku
- Database: Railway PostgreSQL or AWS RDS
- Calibration log: GitHub repository
- MCP server: Expose via HTTP + stdio

---

## Success Metrics (Phase 1)

| Metric | Target | How Measured |
|--------|--------|--------------|
| ACAT accuracy | >80% | Prediction vs actual quality correlation |
| Calibration convergence | Weights stable by week 6 | Log improvement rate |
| Worker satisfaction with matching | >85% | Survey: "Did match feel accurate?" |
| Prediction error (quality) | <0.5 points (on 5-point scale) | MAE of predicted vs actual rating |
| Learning speed | 5-10% improvement per task | Measure accuracy trend over time |

---

## Next Steps

1. **Week 1:** Clone repo, install dependencies, connect to existing ACAT API
2. **Week 2:** Implement calibration storage (GitHub + PostgreSQL)
3. **Week 3:** Compose with RAH MCP, test end-to-end
4. **Week 4:** Deploy + run first 5 tasks
5. **Week 5-6:** Collect data, measure calibration accuracy

---

**Status:** Ready to implement  
**Owner:** Infrastructure Lead  
**Dependencies:** Existing ACAT API (already available)  
**Estimated effort:** 40-60 hours (core implementation)
