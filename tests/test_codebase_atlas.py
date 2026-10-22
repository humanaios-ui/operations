"""Falsifiers for the observational Codebase Atlas boundary."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'architecture' / 'codebase_atlas.py'
SPEC = importlib.util.spec_from_file_location('codebase_atlas_under_test', SOURCE)
atlas = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(atlas)


class AtlasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'config', 'user.name', 'Atlas Test'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'config', 'user.email', 'atlas@example.test'], check=True)
        self.config = self.repo / 'components.json'
        self.config.write_text(json.dumps({'components': [
            {'id': 'core', 'label': 'Core', 'patterns': ['core/*']},
            {'id': 'app', 'label': 'App', 'patterns': ['app/*']},
            {'id': 'workflows', 'label': 'Workflows', 'patterns': ['.github/workflows/*']},
            {'id': 'docs', 'label': 'Docs', 'patterns': ['docs/*']},
        ]}))
        self.write('core/__init__.py', '')
        self.write('core/mod.py', 'X = 1\n')
        self.write('app/main.py', 'import core.mod\nfrom core import mod\n# import nonexistent.fake\n')
        self.write('.github/workflows/check.yml', '# python tools/phantom.py\nrun: python app/main.py\n')
        self.write('docs/README.md', '[source](../core/mod.py)\n[not real](missing.py)\n')
        self.write('IGNORE.secret', 'this untracked file must never be read')
        self.commit()

    def write(self, name, contents):
        p = self.repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contents)

    def commit(self):
        subprocess.run(['git', '-C', str(self.repo), 'add', 'core', 'app', '.github', 'docs', 'components.json'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'commit', '-qm', 'test fixture'], check=True)

    def test_contract_identity_and_no_authority(self):
        graph = atlas.build(self.repo, self.config, 'example/atlas-test')
        self.assertEqual(graph['schema'], atlas.SCHEMA)
        self.assertEqual(graph['authority_effect'], 'NONE')
        self.assertFalse(graph['merge_authority'])
        self.assertTrue(graph['worktree_clean'])
        self.assertTrue(re.fullmatch(r'[a-f0-9]{40}', graph['head_sha']))
        self.assertNotIn('IGNORE.secret', json.dumps(graph))
        self.assertEqual(graph['coverage']['unmapped_files'], 1)  # components.json

    def test_evidenced_edges_and_no_guesswork(self):
        graph = atlas.build(self.repo, self.config, 'example/atlas-test')
        edges={(e['source'],e['target'],e['kind']):e for e in graph['edges']}
        self.assertIn(('app','core','python_import'),edges)
        self.assertIn(('workflows','app','workflow_invokes'),edges)
        self.assertIn(('docs','core','doc_link'),edges)
        self.assertEqual(edges[('app','core','python_import')]['count'],2)
        self.assertTrue(all(a['source']=='app/main.py' for a in edges[('app','core','python_import')]['evidence']))
        self.assertTrue(all('phantom' not in json.dumps(e) for e in edges.values()))

    def test_clean_repo_deterministic(self):
        g1=atlas.build(self.repo,self.config,'example/atlas-test')
        g2=atlas.build(self.repo,self.config,'example/atlas-test')
        self.assertEqual(g1,g2)
        self.assertIn(f'/blob/{g1["head_sha"]}/',g1['nodes'][0]['url'])
        self.assertIn('click core',g1['mermaid'])

    def test_dirty_worktree_does_not_claim_exact_snapshot(self):
        self.write('app/main.py','import core.mod\n# modified')
        g=atlas.build(self.repo,self.config,'example/atlas-test')
        self.assertFalse(g['worktree_clean'])
        self.assertEqual(g['snapshot'],'UNVERIFIED_WORKTREE')
        self.assertFalse(g['merge_authority'])

    def test_unsafe_pattern_fails_closed(self):
        bad=json.loads(self.config.read_text())
        bad['components'][0]['patterns']=['../../.ssh/*']
        self.config.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError,'unsafe'):
            atlas.build(self.repo,self.config,'example/atlas-test')

    def test_bad_repository_and_duplicate_ids_fail(self):
        with self.assertRaises(ValueError):
            atlas.build(self.repo,self.config,'https://evil.example/repo')
        bad=json.loads(self.config.read_text())
        bad['components'].append(bad['components'][0])
        self.config.write_text(json.dumps(bad))
        with self.assertRaises(ValueError):
            atlas.load_config(self.config)

    def test_html_script_escape_and_no_external_js(self):
        graph=atlas.build(self.repo,self.config,'example/atlas-test')
        graph['nodes'][0]['label']='</script><img src=x onerror=alert(1)>'
        page=atlas.render_html(graph)
        self.assertNotIn('</script><img',page)
        self.assertIn('\\u003c/script>',page)
        self.assertNotIn('src="https://',page)
        self.assertNotIn('innerHTML',page)
        self.assertIn('textContent',page)

    def test_static_imports_ignore_strings_and_unresolved(self):
        modules={'core.mod':'core/mod.py'}
        lines='''"import core.mod"\n# import core.mod\nfrom imaginary import ghost\nimport core.mod\n'''
        self.assertEqual(atlas.parse_python_imports('app/main.py',lines,modules),[('core/mod.py',4)])

    def test_empty_docs_link_cannot_claim_real_relation(self):
        self.assertEqual(list(atlas.linked_markdown_paths('docs/README.md',
                          '[ghost](ghost.py) [outside](https://bad.example)',{'docs/README.md'})),[])

    def test_symlinks_and_out_of_repo_paths_not_included(self):
        outside=Path(self.tmp.name).parent/'not-existing-atlas-target'
        symlink=self.repo/'core'/'jump.py'
        symlink.symlink_to(outside)
        subprocess.run(['git','-C',str(self.repo),'add','core/jump.py'],check=True)
        observed=atlas.tracked_files(self.repo)
        self.assertNotIn('core/jump.py',observed)


if __name__ == '__main__':
    unittest.main()
