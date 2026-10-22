#!/usr/bin/env python3
"""Regression tests for the Python 3 revival batch.

Run from the repo root:  python3 -m unittest discover -s tests
Stdlib only, like the rest of CMScout.
"""
import http.server
import os
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestImports(unittest.TestCase):
    def test_full_import_warning_free(self):
        # Every SyntaxWarning is a future SyntaxError: the whole tree must
        # import cleanly with them escalated. Drop stale bytecode first so
        # the warnings can't hide behind a warm __pycache__.
        import shutil
        for dirpath, dirnames, _filenames in os.walk(ROOT):
            for dirname in list(dirnames):
                if dirname == "__pycache__":
                    shutil.rmtree(os.path.join(dirpath, dirname))
        proc = subprocess.run(
            [sys.executable, "-W", "error::SyntaxWarning",
             "-c", "import cmscout.main"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_direct_lib_import(self):
        # lib modules must not depend on import side effects from main.
        proc = subprocess.run(
            [sys.executable, "-c",
             "from cmscout.lib.requester import requester;"
             "from cmscout.lib.threadscanner import ThreadScanner"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestCLI(unittest.TestCase):
    def test_help_exits_zero(self):
        proc = subprocess.run(
            [sys.executable, "cmscout.py", "--help"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("CMScout tool", proc.stdout)

    def test_no_args_exits_one(self):
        proc = subprocess.run(
            [sys.executable, "cmscout.py"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("No options provided", proc.stdout)

    def test_old_cmsmap_name_still_runs(self):
        # CMSmap became CMScout; command lines written for the old name
        # must keep working.
        proc = subprocess.run(
            [sys.executable, "cmsmap.py", "--help"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("CMScout tool", proc.stdout)
        self.assertIn("cmsmap.py is now cmscout.py", proc.stderr)


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    seen_paths = []

    def _serve(self):
        _FixtureHandler.seen_paths.append(self.path)
        if "missing" in self.path:
            self.send_response(404)
        else:
            self.send_response(200)
        body = b"<html>fixture</html>"
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = _serve

    def log_message(self, *args):
        pass


class TestRequester(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cmscout.lib.requester import requester
        cls.requester = requester
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), _FixtureHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()

    def test_nasty_plugin_name_does_not_raise(self):
        # Issues #19/#22/#25/#26: names with spaces or control chars
        # crashed scans with "URL can't contain control characters".
        base = "http://127.0.0.1:%d" % self.port
        nasty = base + "/wp-content/plugins/my plugin/\x01/"
        self.requester.request(nasty, data=None)  # must not raise
        self.assertEqual(self.requester.status_code, 200)

    def test_nasty_url_arrives_quoted(self):
        seen = _FixtureHandler.seen_paths
        self.assertTrue(seen)
        last = seen[-1]
        self.assertNotRegex(last, r"[\x00-\x20\x7f]")
        self.assertIn("my%20plugin", last)

    def test_failed_request_sets_empty_state(self):
        # A dead host must not raise and must not leave stale/None state:
        # scanners call len(htmltext) unconditionally.
        self.requester.request("http://127.0.0.1:1/", data=None)
        self.assertIsNone(self.requester.status_code)
        self.assertEqual(self.requester.htmltext, "")

    def test_failed_request_is_not_a_find(self):
        # Transport failure must not look like a discovered plugin.
        import queue
        import time
        from cmscout.lib.threadscanner import ThreadScanner
        found = []
        q = queue.Queue()
        t = ThreadScanner("http://127.0.0.1:1", "/wp-content/plugins/",
                          "/", found, 404, [], q)
        t.daemon = True
        t.start()
        q.put("anything")
        deadline = time.time() + 30
        while q.unfinished_tasks and time.time() < deadline:
            time.sleep(0.1)
        self.assertEqual(q.unfinished_tasks, 0, "worker died without task_done()")
        self.assertEqual(found, [])

    def test_concurrent_scan_finds_exactly(self):
        # Scan workers must not share one Requester: shared response
        # state made workers misread each other's results (missed finds).
        import queue
        from cmscout.lib.threadscanner import ThreadScanner
        base = "http://127.0.0.1:%d" % self.port
        found = []
        q = queue.Queue()
        for _u in range(5):
            t = ThreadScanner(base, "/wp-content/plugins/", "/",
                              found, 404, [], q)
            t.daemon = True
            t.start()
        q.put("hello")
        for i in range(19):
            q.put("missing%d" % i)
        q.join()
        self.assertEqual(sorted(found), ["hello"])


class TestSearchsploit(unittest.TestCase):
    def _stub(self, tmp, help_text):
        path = os.path.join(tmp, "searchsploit")
        with open(path, "w") as f:
            f.write("#!/bin/sh\ncat <<'EOF'\n%s\nEOF\n" % help_text)
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        return path

    def test_modern_flag(self):
        # Issue #35: searchsploit renamed --colour to --disable-colour.
        from cmscout.lib import exploitdbsearch
        with tempfile.TemporaryDirectory() as tmp:
            self._stub(tmp, "Options:\n  --disable-colour  Disable colour\n")
            with mock.patch.dict(os.environ,
                                 {"PATH": tmp + ":" + os.environ.get("PATH", "")}):
                exploitdbsearch._colour_flag_cache.clear()
                flag = exploitdbsearch.searchsploit_colour_flag("searchsploit")
                self.assertEqual(flag, " --disable-colour ")

    def test_legacy_flag(self):
        from cmscout.lib import exploitdbsearch
        with tempfile.TemporaryDirectory() as tmp:
            self._stub(tmp, "Options:\n  --colour  Enable colour\n")
            with mock.patch.dict(os.environ,
                                 {"PATH": tmp + ":" + os.environ.get("PATH", "")}):
                exploitdbsearch._colour_flag_cache.clear()
                flag = exploitdbsearch.searchsploit_colour_flag("searchsploit")
                self.assertEqual(flag, " --colour ")

    def test_strip_ansi(self):
        from cmscout.lib.exploitdbsearch import strip_ansi
        self.assertEqual(strip_ansi("\x1b[32m12345\x1b[0m"), "12345")


if __name__ == "__main__":
    unittest.main()
