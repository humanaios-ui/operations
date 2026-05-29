DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'acat_submission_purity_check'
      AND conrelid = 'public.acat_assessments_v1'::regclass
  ) THEN
    ALTER TABLE public.acat_assessments_v1
      ADD CONSTRAINT acat_submission_purity_check
      CHECK (submission_purity IN (
        'clean',
        'anchored',
        'contaminated',
        'unknown',
        'agent_self_only'
      ));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'acat_learning_index_cap_check'
      AND conrelid = 'public.acat_assessments_v1'::regclass
  ) THEN
    ALTER TABLE public.acat_assessments_v1
      ADD CONSTRAINT acat_learning_index_cap_check
      CHECK (learning_index IS NULL OR learning_index <= 2.0);
  END IF;
END $$;
