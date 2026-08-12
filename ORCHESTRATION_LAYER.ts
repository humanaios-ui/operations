/**
 * ORCHESTRATION LAYER
 *
 * Chains RentAHuman MCP + ACAT MCP
 * Real-time fair task matching with continuous learning
 *
 * Purpose: Automate the matching → invitation → completion → calibration loop
 */

import { RAHClient } from "rentahuman-mcp";
import { ACATClient } from "acat-mcp";
import { Logger } from "./utils/logger";
import { Database } from "./database";

interface Task {
  id: string;
  title: string;
  description: string;
  budget: number;
  skills_required: string[];
  task_type: "research" | "writing" | "analysis" | "validation" | "design";
  deadline: string;
}

interface Worker {
  id: string;
  name: string;
  skills: string[];
  hourly_rate: number;
  rating: number;
  prior_jobs: number;
  bio: string;
}

interface Match {
  worker_id: string;
  task_id: string;
  match_score: number;
  reasoning: string;
  predicted_quality: number;
  predicted_completion_days: number;
  status: "invited" | "accepted" | "completed" | "submitted";
  actual_quality?: number;
  actual_completion_days?: number;
}

/**
 * ORCHESTRATION MAIN CLASS
 */
export class FairTaskOrchestrator {
  private rah: RAHClient;
  private acat: ACATClient;
  private db: Database;
  private logger: Logger;
  private matches: Map<string, Match> = new Map();

  constructor() {
    this.rah = new RAHClient(process.env.RAH_API_KEY!);
    this.acat = new ACATClient(process.env.ACAT_API_URL!);
    this.db = new Database(process.env.DATABASE_URL!);
    this.logger = new Logger("FairTaskOrchestrator");
  }

  /**
   * PHASE 1: DISCOVER
   * When a new task is posted (on GitHub, Gitcoin, OpenCollective)
   * Orchestrator discovers it and queries RAH for matching workers
   */
  async discoverAndMatch(task: Task): Promise<void> {
    this.logger.info(`🔍 Discovering workers for task: ${task.id}`, {
      title: task.title,
      budget: task.budget,
      skills: task.skills_required,
    });

    try {
      // Step 1: Query RAH for workers with matching skills
      const workers = await this.rah.search_humans({
        skills: task.skills_required,
        availability: "immediate",
        rating_min: 4.0, // Only 4+ star workers
      });

      this.logger.info(`Found ${workers.length} potential workers`, {
        task_id: task.id,
      });

      // Step 2: Assess each worker with ACAT
      const assessments = await this.assessWorkers(workers, task);

      // Step 3: Rank and invite top 3
      await this.rankAndInvite(task, workers, assessments);
    } catch (error) {
      this.logger.error(`Failed to discover/match for task ${task.id}`, error);
      throw error;
    }
  }

  /**
   * PHASE 2: ASSESS (Real-time)
   * For each worker, run ACAT assessment against task requirements
   */
  private async assessWorkers(
    workers: Worker[],
    task: Task
  ): Promise<Map<string, any>> {
    this.logger.info(
      `🧠 Assessing ${workers.length} workers with ACAT...`,
      {
        task_id: task.id,
        task_type: task.task_type,
      }
    );

    const assessments = new Map();

    // Task requirements vary by task type
    const taskRequirements = this.getTaskRequirements(task.task_type);

    // Assess in parallel (speed up process)
    const assessmentPromises = workers.map((worker) =>
      this.acat.assess_worker({
        worker_profile: worker,
        task_requirements: taskRequirements,
        historical_data: null, // Optional: fetch worker history from DB
      })
    );

    const results = await Promise.all(assessmentPromises);

    // Store assessments by worker ID
    results.forEach((assessment, idx) => {
      assessments.set(workers[idx].id, assessment);
      this.logger.info(`Assessed ${workers[idx].name}`, {
        worker_id: workers[idx].id,
        match_score: assessment.match_score,
        reasoning: assessment.reasoning,
      });
    });

    return assessments;
  }

  /**
   * PHASE 3: RANK & INVITE
   * Score all assessments and invite top 3 matched workers
   */
  private async rankAndInvite(
    task: Task,
    workers: Worker[],
    assessments: Map<string, any>
  ): Promise<void> {
    this.logger.info(`📊 Ranking workers...`, { task_id: task.id });

    // Convert to array for sorting
    const scoredWorkers = workers.map((w) => ({
      ...w,
      assessment: assessments.get(w.id),
    }));

    // Use ACAT's score_match tool to rank
    const ranked = await this.acat.score_match({
      task_id: task.id,
      task_requirements: this.getTaskRequirements(task.task_type),
      worker_assessments: Array.from(assessments.values()),
      top_n: 3, // Invite top 3
    });

    this.logger.info(`Top 3 matches ranked`, {
      task_id: task.id,
      ranked_workers: ranked.ranked_workers.map((r) => ({
        rank: r.rank,
        worker_id: r.worker_id,
        match_score: r.match_score,
      })),
    });

    // Step 1: Create bounty on RAH
    const bounty = await this.rah.create_bounty({
      title: task.title,
      description: task.description,
      budget: task.budget,
      skills_required: task.skills_required,
      deadline: task.deadline,
      payment_method: "open_collective", // Route to our Open Collective
      tags: [task.task_type, "fair-labor", "transparency"],
    });

    this.logger.info(`Bounty created on RAH`, {
      bounty_id: bounty.id,
      task_id: task.id,
    });

    // Step 2: Invite top 3 workers with personalized messages
    for (const rankedWorker of ranked.ranked_workers) {
      const invitation = await this.rah.invite_workers({
        bounty_id: bounty.id,
        worker_ids: [rankedWorker.worker_id],
        personal_message: rankedWorker.invitation_message,
        priority: "high",
      });

      // Store match record for later tracking
      const match: Match = {
        worker_id: rankedWorker.worker_id,
        task_id: task.id,
        match_score: rankedWorker.match_score,
        reasoning: rankedWorker.reasoning,
        predicted_quality: assessments.get(rankedWorker.worker_id)
          .predicted_quality,
        predicted_completion_days: assessments.get(rankedWorker.worker_id)
          .predicted_completion_days,
        status: "invited",
      };

      this.matches.set(`${task.id}:${rankedWorker.worker_id}`, match);

      // Log to DB
      await this.db.insertMatch(match);

      this.logger.info(
        `Invited ${rankedWorker.worker_id} to ${task.id}`,
        {
          bounty_id: bounty.id,
          match_score: rankedWorker.match_score,
        }
      );
    }
  }

  /**
   * PHASE 4: MONITOR & COLLECT FEEDBACK (Continuous)
   * Poll RAH for task completion and collect outcomes
   */
  async monitorAndCollect(): Promise<void> {
    this.logger.info(`📋 Monitoring active tasks...`);

    // Get all matches that are still "in progress" (invited/accepted/completed)
    const activeMatches = await this.db.getActiveMatches();

    for (const match of activeMatches) {
      try {
        // Check status on RAH
        const submissions = await this.rah.get_submissions(match.task_id);

        if (!submissions || submissions.length === 0) {
          continue; // No submission yet
        }

        // Task completed!
        const submission = submissions[0];
        const employer_rating = submission.quality_rating || 4.5; // Default if not provided
        const completion_days = submission.completion_time_days;
        const satisfaction = submission.satisfaction || 4.0;

        this.logger.info(`Task completed`, {
          task_id: match.task_id,
          worker_id: match.worker_id,
          quality: employer_rating,
          days: completion_days,
        });

        // Step 1: Update match record
        match.actual_quality = employer_rating;
        match.actual_completion_days = completion_days;
        match.status = "submitted";

        // Step 2: Calibrate ACAT with feedback
        await this.calibrateACATWithFeedback(match, satisfaction);

        // Step 3: Log outcome
        await this.db.updateMatch(match);

        // Step 4: Process payment
        await this.processPayment(match, submission);
      } catch (error) {
        this.logger.error(
          `Failed to collect feedback for ${match.task_id}`,
          error
        );
      }
    }
  }

  /**
   * PHASE 5: CALIBRATE (Real-time Learning)
   * Feed outcomes back into ACAT for model recalibration
   */
  private async calibrateACATWithFeedback(
    match: Match,
    satisfaction: number
  ): Promise<void> {
    this.logger.info(`🎓 Calibrating ACAT with feedback...`, {
      task_id: match.task_id,
      worker_id: match.worker_id,
    });

    // Get ACAT assessment data for this match
    const assessment = await this.db.getAssessment(
      match.task_id,
      match.worker_id
    );

    // Call learn_from_feedback tool
    const calibrationResult = await this.acat.learn_from_feedback({
      worker_id: match.worker_id,
      task_id: match.task_id,
      task_type: (await this.db.getTask(match.task_id)).task_type,
      acat_prediction: {
        match_score: match.match_score,
        predicted_quality: match.predicted_quality,
        predicted_completion_days: match.predicted_completion_days,
      },
      actual_outcome: {
        quality_rating: match.actual_quality!,
        completion_time_days: match.actual_completion_days!,
        satisfaction: satisfaction,
        completed: true,
      },
    });

    this.logger.info(`ACAT calibrated`, {
      task_id: match.task_id,
      prediction_error: Math.abs(
        match.predicted_quality - match.actual_quality!
      ),
      accuracy_improvement: calibrationResult.accuracy_improvement,
    });

    // Log calibration to GitHub (transparency)
    await this.db.logCalibration({
      timestamp: new Date().toISOString(),
      task_id: match.task_id,
      worker_id: match.worker_id,
      prediction_accuracy: Math.abs(
        match.predicted_quality - match.actual_quality!
      ),
      new_weights: calibrationResult.new_weights,
    });
  }

  /**
   * PAYMENT PROCESSING
   * Route funds from Open Collective to worker
   */
  private async processPayment(match: Match, submission: any): Promise<void> {
    this.logger.info(`💰 Processing payment...`, {
      task_id: match.task_id,
      worker_id: match.worker_id,
    });

    // Get task budget
    const task = await this.db.getTask(match.task_id);

    // Calculate payment breakdown
    const employer_funds = task.budget;
    const stripe_fee = employer_funds * 0.022; // 2.2% Stripe
    const coordination_fee = employer_funds * 0.05; // 5% Fair Brokerage
    const worker_payment = employer_funds - stripe_fee - coordination_fee;
    const verification_bonus = coordination_fee * 0.4; // 40% of our fee back to worker

    // Update totals
    const final_worker_payment = worker_payment + verification_bonus;

    this.logger.info(`Payment breakdown`, {
      employer_funds,
      stripe_fee: stripe_fee.toFixed(2),
      coordination_fee: coordination_fee.toFixed(2),
      worker_payment: final_worker_payment.toFixed(2),
    });

    // Process via payment service (Open Collective / Stripe)
    await this.db.logPayment({
      task_id: match.task_id,
      worker_id: match.worker_id,
      amount: final_worker_payment,
      status: "pending",
    });

    // TODO: Call payment processor
    // await paymentService.transfer(worker_id, final_worker_payment);
  }

  /**
   * HELPER: Get task requirements by type
   */
  private getTaskRequirements(
    task_type: string
  ): Record<string, number | string> {
    const requirements = {
      research: {
        consistency_needed: 0.9,
        truthfulness_needed: 0.95,
        sycophancy_tolerance: 0.3,
        harm_tolerance: 0.2,
        task_type: "research",
      },
      writing: {
        consistency_needed: 0.85,
        truthfulness_needed: 0.85,
        sycophancy_tolerance: 0.4,
        harm_tolerance: 0.25,
        task_type: "writing",
      },
      analysis: {
        consistency_needed: 0.92,
        truthfulness_needed: 0.9,
        sycophancy_tolerance: 0.25,
        harm_tolerance: 0.15,
        task_type: "analysis",
      },
      validation: {
        consistency_needed: 0.95,
        truthfulness_needed: 0.98,
        sycophancy_tolerance: 0.2,
        harm_tolerance: 0.1,
        task_type: "validation",
      },
      design: {
        consistency_needed: 0.8,
        truthfulness_needed: 0.8,
        sycophancy_tolerance: 0.5,
        harm_tolerance: 0.3,
        task_type: "design",
      },
    };

    return requirements[task_type] || requirements.research;
  }
}

/**
 * POLLING LOOP
 * Runs continuously to discover tasks & monitor outcomes
 */
export async function startOrchestrationLoop(): Promise<void> {
  const orchestrator = new FairTaskOrchestrator();
  const logger = new Logger("OrchestrationLoop");

  logger.info("🚀 Starting orchestration loop...");

  // Poll every 5 minutes
  const POLL_INTERVAL = 5 * 60 * 1000; // 5 minutes

  const loop = async () => {
    try {
      // Step 1: Check for new tasks (from GitHub, Gitcoin, OpenCollective)
      const newTasks = await fetchNewTasks();
      for (const task of newTasks) {
        await orchestrator.discoverAndMatch(task);
      }

      // Step 2: Monitor active tasks and collect feedback
      await orchestrator.monitorAndCollect();
    } catch (error) {
      logger.error("Error in orchestration loop", error);
    }

    // Schedule next iteration
    setTimeout(loop, POLL_INTERVAL);
  };

  // Start the loop
  loop();
}

/**
 * FETCH NEW TASKS
 * Check GitHub Issues, Gitcoin bounties, OpenCollective for new tasks
 */
async function fetchNewTasks(): Promise<Task[]> {
  // TODO: Implement
  // - Check GitHub Issues with label "fair-brokerage-task"
  // - Check Gitcoin bounties API
  // - Check OpenCollective tasks
  return [];
}

/**
 * EXAMPLE USAGE
 */
export async function main() {
  // Example: Manually trigger orchestration for a single task
  const orchestrator = new FairTaskOrchestrator();

  const exampleTask: Task = {
    id: "task_001",
    title: "ACAT Validation Study ($750)",
    description: "Analyze ACAT scores across 10 research tasks...",
    budget: 750,
    skills_required: ["research", "statistics"],
    task_type: "research",
    deadline: "2026-09-15",
  };

  // Discover and match
  await orchestrator.discoverAndMatch(exampleTask);

  // Start monitoring loop (runs in background)
  // In production, this would be a scheduled job
  // await startOrchestrationLoop();
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}
