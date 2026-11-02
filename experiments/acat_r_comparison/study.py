#!/usr/bin/env python3
"""ACAT-R: GNER-E1 unmodified runtime, fair same-input conventional comparison.

Expected labels proposed from documented contract, NOT independently ratified.
All external metadata is constructed. No live Github API, Gmail or credentials.
"""
import hashlib, json, pathlib, subprocess, sys, unittest
from types import SimpleNamespace

ROOT=pathlib.Path(__file__).resolve().parents[2]
SOURCE=ROOT/"tools/gner_verify_e1.py"
TESTS=ROOT/"tests/test_gner_verify_e1.py"
SOURCE_BLOB="8290c51cd75c7de78a226770936a8f48766c24f0"
TEST_BLOB="8517a93f346e31a392ed7c7234434f37b3e15237"
OUT=ROOT/"acatr-gner-evidence"
def sha(v): return hashlib.sha256(v).hexdigest()
def encoded(v): return (json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def validate(cond,msg):
    if not cond: raise ValueError(msg)
def build():
    rows=[]
    def add(n,expected,lead=None,canonical=None):
        l={"state":"EMAIL_OBSERVED_UNVERIFIED","repository":"humanaios-ui/operations",
           "run_id":41085749811,"sha_prefix":"8ec744a","workflow":"quality-baseline",
           "kind":"WORKFLOW_FAILURE_LEAD","pr":None}
        c={"id":41085749811,"repository":{"full_name":"humanaios-ui/operations"},
           "head_sha":"8ec744a1cba7e7fad79b8589829fd460f4527f33",
           "name":"quality-baseline","event":"pull_request","status":"completed",
           "conclusion":"failure","pull_requests":[]}
        l.update(lead or {});c.update(canonical or {})
        rows.append({"id":n,"expected":expected,"lead":l,"canonical":c})
    add("valid_failure","CANONICAL_VERIFIED")
    add("wrong_repo","CONFLICT",canonical={"repository":{"full_name":"other/repo"}})
    add("wrong_run","CONFLICT",canonical={"id":5})
    add("wrong_sha","CONFLICT",lead={"sha_prefix":"deadbee"})
    add("nonterminal","ABSTAIN",canonical={"status":"in_progress","conclusion":None})
    add("wrong_workflow","CONFLICT",lead={"workflow":"fake-gate"})
    add("failure_claim_vs_success","CONFLICT",canonical={"conclusion":"success"})
    add("unknown_pr","ABSTAIN",lead={"pr":765})
    add("valid_success","CANONICAL_VERIFIED",lead={"kind":"NOTIFICATION_LEAD"},canonical={"conclusion":"success"})
    add("valid_review","CANONICAL_VERIFIED",lead={"kind":"REVIEW_LEAD","pr":765},canonical={"pull_requests":[{"number":765}]})
    add("invalid_lead_state","CONFLICT",lead={"state":"VERIFIED"})
    add("invalid_lead_repo","CONFLICT",lead={"repository":"forged/org"})
    add("invalid_missing_run","ABSTAIN",lead={"run_id":None})
    add("invalid_zero_run","ABSTAIN",lead={"run_id":0})
    add("invalid_negative_run","ABSTAIN",lead={"run_id":-5})
    add("invalid_canonical_sha","CONFLICT",canonical={"head_sha":"x"*40})
    add("invalid_canonical_repo","CONFLICT",canonical={"repository":{}})
    add("unsupported_event","CONFLICT",canonical={"event":"fork"})
    add("missing_workflow","CONFLICT",canonical={"name":None})
    add("missing_prs","ABSTAIN",lead={"pr":765},canonical={"pull_requests":None})
    add("other_pr","ABSTAIN",lead={"pr":765},canonical={"pull_requests":[{"number":764}]})
    add("skip_terminal","CANONICAL_VERIFIED",lead={"kind":"NOTIFICATION_LEAD"},canonical={"conclusion":"skipped"})
    add("neutral_terminal","CANONICAL_VERIFIED",lead={"kind":"NOTIFICATION_LEAD"},canonical={"conclusion":"neutral"})
    add("invalid_status","ABSTAIN",canonical={"status":"queued"})
    add("unsupported_conclusion","ABSTAIN",canonical={"conclusion":"action_required"})
    add("unknown_run_id_as_str","ABSTAIN",lead={"run_id":"41085749811"})
    add("type_canonical_bool_id","CONFLICT",lead={"run_id":1},canonical={"id":True})
    add("type_lead_bool_id","ABSTAIN",lead={"run_id":True},canonical={"id":1})
    add("type_boolean_pr_in_canonical","ABSTAIN",lead={"pr":1},canonical={"pull_requests":[{"number":True}]})
    add("type_lead_bool_pr","ABSTAIN",lead={"pr":True},canonical={"pull_requests":[{"number":1}]})
    validate(len(rows)==30 and len({c["id"] for c in rows})==30,"case count")
    return rows
def worker():
    sys.path.insert(0,str(ROOT/"tools"))
    from gner_verify_e1 import reconcile
    cases=json.loads(sys.stdin.buffer.read(150000))
    results=[]
    for c in cases:
        try:
            r=reconcile(c["lead"],c["canonical"])
            results.append({"id":c["id"],"state":r.get("state"),
                            "authority":r.get("authority"),"execution":r.get("execution")})
        except Exception as exc:
            results.append({"id":c["id"],"state":"EXCEPTION",
                            "authority":None,"execution":None,"error":type(exc).__name__})
    sys.stdout.buffer.write(encoded(results))
def run_phase(cases):
    p=subprocess.run([sys.executable,"-I","-S",str(pathlib.Path(__file__).resolve()),"--worker"],
                     input=encoded(cases),capture_output=True,timeout=12)
    validate(p.returncode==0,"runtime subprocess failed: "+p.stderr.decode(errors="replace")[:300])
    obj=json.loads(p.stdout)
    validate(len(obj)==len(cases) and len({x["id"] for x in obj})==len(cases),"invalid output length or duplicate")
    return SimpleNamespace(raw=p.stdout,rows=obj,input_hash=sha(encoded(cases)),output_hash=sha(p.stdout))
def assess(cases,output):
    indexed={r["id"]:r for r in output.rows}
    bad=[]
    for c in cases:
        r=indexed[c["id"]]
        if (r["state"]!=c["expected"] or r["authority"]!="NONE" or r["execution"]!="DISABLED"):
            bad.append({"id":c["id"],"expected":c["expected"],"observed":r})
    return bad
def baseline():
    p=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests",
                      "-p","test_gner_verify_e1.py","-v"],cwd=ROOT,
                      capture_output=True,text=True,timeout=40)
    (OUT/"conventional_existing_10.log").write_text(p.stdout+p.stderr)
    validate(p.returncode==0,"pre-existing standard tests not passing")
def fair_conventional(cases,rows):
    seen={r["id"]:r for r in rows}
    cls=type("EqualWorkloadConventional",(unittest.TestCase,),{})
    for c in cases:
        def check(self,x=c):
            r=seen[x["id"]]
            self.assertEqual(r["state"],x["expected"])
            self.assertEqual(r["authority"],"NONE")
            self.assertEqual(r["execution"],"DISABLED")
        setattr(cls,"test_"+c["id"],check)
    import io
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    (OUT/"conventional_equal_30.log").write_text(stream.getvalue())
    return sorted([t._testMethodName[5:] for t,_ in result.failures+result.errors])
def main():
    p=subprocess.run(["git","hash-object",str(SOURCE)],cwd=ROOT,capture_output=True,text=True,check=True)
    q=subprocess.run(["git","hash-object",str(TESTS)],cwd=ROOT,capture_output=True,text=True,check=True)
    validate(p.stdout.strip()==SOURCE_BLOB and q.stdout.strip()==TEST_BLOB,"original source or tests changed")
    cases=build()
    OUT.mkdir(exist_ok=False)
    rubric=encoded(cases);(OUT/"reference_proposed.json").write_bytes(rubric)
    commitment={"source_sha256":sha(SOURCE.read_bytes()),"conventional_test_sha256":sha(TESTS.read_bytes()),
                "rubric_sha256":sha(rubric),"P1_input_sha256":sha(encoded(cases[:8])),
                "authority_effect":"NONE","label_state":"PENDING_INDEPENDENT_REVIEW"}
    (OUT/"P1_COMMIT.json").write_bytes(encoded(commitment))
    p1=run_phase(cases[:8]);(OUT/"P1_stdout.json").write_bytes(p1.raw)
    baseline()
    p2=run_phase(cases);(OUT/"P2_stdout.json").write_bytes(p2.raw)
    p3=run_phase(cases);(OUT/"P3_stdout.json").write_bytes(p3.raw)
    validate(p2.raw==p3.raw,"same-input byte replay mismatch")
    acatr=assess(cases,p2);conv=fair_conventional(cases,p2.rows)
    flags=sorted(x["id"] for x in acatr)
    validate(flags==conv,"fair comparison divergence")
    false_promotions=[x["id"] for x in acatr if x["expected"]!="CANONICAL_VERIFIED" and x["observed"]["state"]=="CANONICAL_VERIFIED"]
    result={
        "schema":"humanaios.acat-r.equal-workload.v0.1",
        "status":"PROVISIONAL_REFERENCE_LABELS_NEED_INDEPENDENT_REVIEW",
        "target":"Unmodified GNER-E1 reconcile (offline pure function)",
        "source_git_blob":SOURCE_BLOB,"source_sha256":commitment["source_sha256"],
        "conventional_blob":TEST_BLOB,"rubric_sha256":sha(rubric),
        "P1":{"cases":8,"nonconformances":assess(cases[:8],p1),"output_sha256":p1.output_hash},
        "P2":{"cases":30,"nonconformances":acatr,"output_sha256":p2.output_hash},
        "P3":{"cases":30,"output_sha256":p3.output_hash,"byte_identical":True},
        "conventional_baseline":{"preexisting_cases":10,"passed":True},
        "conventional_equal":{"cases":30,"detected":conv},
        "acatr_equal":{"cases":30,"detected":flags},
        "suspected_type_schema_false_promotions":false_promotions,
        "acatr_detection_advantage_on_equal_inputs":0,
        "measured_false_alarm_rate":"UNDETERMINED: oracle labels not independently approved",
        "captures_real_github_data":False,"auth_path_tested":False,
        "authority_effect":"NONE","can_authorize":False,"admission":"HOLD",
        "limitations":[
            "Constructed canonical metadata; the authenticated verify_lead entry point was not tested.",
            "Boolean-ID cases are proposed stricter schema checks, not proven GitHub API inputs.",
            "Reference labels written by investigator; require independent adjudication before publishing bug counts.",
            "Both methods share the same source, observations and expected labels; added detection is zero.",
            "P3 is repeated input with unchanged code, not correction, recovery or learning."
        ]}
    (OUT/"report.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"P1":8,"P2":30,"P3":30,
                      "same_workload_flags":flags,"fair_conventional_flags":conv,
                      "false_promotions":false_promotions,"replay":True,
                      "detection_advantage":0,"admission":"HOLD"},sort_keys=True))
if __name__=="__main__":
    if sys.argv[1:]==["--worker"]:worker()
    elif sys.argv[1:]==["--run-owned-offline"]:main()
    else: raise SystemExit("Use --run-owned-offline or --worker")
