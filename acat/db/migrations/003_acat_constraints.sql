ALTER TABLE public.acat_assessments_v1
  ADD CONSTRAINT acat_submission_purity_check
  CHECK (submission_purity IN ('clean', 'anchored', 'contaminated', 'unknown'));

ALTER TABLE public.acat_assessments_v1
  ADD CONSTRAINT acat_learning_index_cap_check
  CHECK (learning_index IS NULL OR learning_index <= 2.0);
