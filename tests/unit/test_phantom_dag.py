"""
Unit tests for the Phantom DAG Orchestrator module.

Tests: Enums, dataclasses, CryptoEngine, ClassificationEngine, DAGExecutor.
"""


import pytest

from phantom.pipeline.phantom_dag import (
    Classification,
    ClassificationEngine,
    CryptoEngine,
    DAGExecutor,
    DAGTask,
    FileFingerprint,
    FileRecord,
    PhantomLogger,
    PipelineContext,
    SanitizationEngine,
    SanitizationPolicy,
    SensitiveFinding,
    Sensitivity,
    TaskStatus,
)

pytestmark = pytest.mark.unit


class TestEnums:
    """Test enum definitions."""

    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.BLOCKED.value == "blocked"

    def test_classification_values(self):
        assert Classification.DOCUMENTS.value == "documents"
        assert Classification.CODE.value == "code"
        assert Classification.IMAGES.value == "images"
        assert Classification.SENSITIVE.value == "sensitive"
        assert Classification.QUARANTINE.value == "quarantine"

    def test_sensitivity_levels(self):
        assert Sensitivity.PUBLIC.value == 0
        assert Sensitivity.TOP_SECRET.value == 4
        assert Sensitivity.RESTRICTED.value == 5
        assert Sensitivity.PUBLIC.value < Sensitivity.TOP_SECRET.value

    def test_sanitization_policy(self):
        assert SanitizationPolicy.NONE.value == "none"
        assert SanitizationPolicy.REDACT_PII.value == "redact_pii"


class TestFileFingerprint:
    """Test FileFingerprint dataclass."""

    def test_construction(self):
        fp = FileFingerprint(
            sha256="abc123",
            blake3="def456",
            xxhash="ghi789",
            size=1024,
            created_at="2024-01-01T00:00:00",
            nonce="aabb",
        )
        assert fp.sha256 == "abc123"
        assert fp.size == 1024

    def test_to_dict(self):
        fp = FileFingerprint(
            sha256="a", blake3="b", xxhash="c", size=100,
            created_at="2024-01-01", nonce="x",
        )
        d = fp.to_dict()
        assert d["sha256"] == "a"
        assert d["size"] == 100
        assert isinstance(d, dict)

    def test_verify_against_match(self):
        fp1 = FileFingerprint("sha1", "b1", "x1", 100, "t1")
        fp2 = FileFingerprint("sha1", "b2", "x2", 100, "t2")
        assert fp1.verify_against(fp2) is True

    def test_verify_against_mismatch_sha(self):
        fp1 = FileFingerprint("sha1", "b", "x", 100, "t")
        fp2 = FileFingerprint("sha2", "b", "x", 100, "t")
        assert fp1.verify_against(fp2) is False

    def test_verify_against_mismatch_size(self):
        fp1 = FileFingerprint("sha1", "b", "x", 100, "t")
        fp2 = FileFingerprint("sha1", "b", "x", 200, "t")
        assert fp1.verify_against(fp2) is False


class TestSensitiveFinding:
    """Test SensitiveFinding dataclass."""

    def test_construction(self):
        finding = SensitiveFinding(
            pattern_type="regex",
            pattern_name="email",
            count=3,
            line_numbers=[1, 5, 10],
            risk_score=0.3,
        )
        assert finding.count == 3
        assert finding.risk_score == 0.3

    def test_defaults(self):
        finding = SensitiveFinding(
            pattern_type="regex", pattern_name="test", count=1,
        )
        assert finding.line_numbers == []
        assert finding.samples == []
        assert finding.risk_score == 0.0


class TestFileRecord:
    """Test FileRecord dataclass."""

    def test_construction(self):
        fp = FileFingerprint("sha", "blake", "xx", 500, "now")
        record = FileRecord(
            record_id="r1",
            original_path="/tmp/test.txt",
            original_name="test.txt",
            pseudonym="PH-abc-def.txt",
            classification="documents",
            sensitivity=0,
            mime_type="text/plain",
            extension=".txt",
            fingerprint_input=fp,
        )
        assert record.record_id == "r1"
        assert record.classification == "documents"
        assert record.sanitization_applied == "none"

    def test_to_dict(self):
        fp = FileFingerprint("sha", "blake", "xx", 500, "now")
        record = FileRecord(
            record_id="r1",
            original_path="/tmp/test.txt",
            original_name="test.txt",
            pseudonym="PH-abc.txt",
            classification="code",
            sensitivity=1,
            mime_type="text/x-python",
            extension=".py",
            fingerprint_input=fp,
        )
        d = record.to_dict()
        assert d["record_id"] == "r1"
        assert isinstance(d["fingerprint_input"], dict)
        assert isinstance(d["tags"], list)


class TestDAGTask:
    """Test DAGTask dataclass."""

    def test_construction(self):
        task = DAGTask(
            task_id="t1",
            name="test_task",
            func=lambda **kw: "done",
        )
        assert task.task_id == "t1"
        assert task.status == TaskStatus.PENDING
        assert task.dependencies == []

    def test_duration_no_times(self):
        task = DAGTask(task_id="t1", name="test", func=lambda **kw: None)
        assert task.duration == 0.0

    def test_duration_with_times(self):
        task = DAGTask(task_id="t1", name="test", func=lambda **kw: None)
        task.start_time = 100.0
        task.end_time = 105.5
        assert task.duration == pytest.approx(5.5)


class TestCryptoEngine:
    """Test CryptoEngine operations."""

    def test_compute_fingerprint(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")
        fp = CryptoEngine.compute_fingerprint(test_file)
        assert len(fp.sha256) == 64
        assert fp.size == 13
        assert fp.nonce != ""

    def test_fingerprint_consistency(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Consistent content")
        fp1 = CryptoEngine.compute_fingerprint(test_file)
        fp2 = CryptoEngine.compute_fingerprint(test_file)
        assert fp1.sha256 == fp2.sha256
        assert fp1.size == fp2.size

    def test_generate_pseudonym(self):
        pseudonym = CryptoEngine.generate_pseudonym("/tmp/test.txt", ".txt")
        assert pseudonym.startswith("PH-")
        assert pseudonym.endswith(".txt")

    def test_generate_pseudonym_different_files(self):
        p1 = CryptoEngine.generate_pseudonym("/tmp/a.txt", ".txt")
        p2 = CryptoEngine.generate_pseudonym("/tmp/b.txt", ".txt")
        # Different paths should produce different pseudonyms
        assert p1 != p2

    def test_verify_integrity_pass(self, tmp_path):
        test_file = tmp_path / "verify.txt"
        test_file.write_text("Integrity check")
        fp = CryptoEngine.compute_fingerprint(test_file)
        assert CryptoEngine.verify_integrity(test_file, fp) is True

    def test_verify_integrity_fail(self, tmp_path):
        test_file = tmp_path / "verify.txt"
        test_file.write_text("Original content")
        fp = CryptoEngine.compute_fingerprint(test_file)
        test_file.write_text("Modified content")
        assert CryptoEngine.verify_integrity(test_file, fp) is False


class TestClassificationEngine:
    """Test ClassificationEngine."""

    def test_detect_by_extension_python(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')")
        mime, cls = ClassificationEngine.detect_by_extension(py_file)
        assert cls == Classification.CODE

    def test_detect_by_extension_markdown(self, tmp_path):
        md_file = tmp_path / "readme.md"
        md_file.write_text("# Hello")
        mime, cls = ClassificationEngine.detect_by_extension(md_file)
        assert cls == Classification.DOCUMENTS

    def test_detect_by_extension_json(self, tmp_path):
        json_file = tmp_path / "data.json"
        json_file.write_text("{}")
        mime, cls = ClassificationEngine.detect_by_extension(json_file)
        assert cls == Classification.DATA

    def test_detect_by_extension_unknown(self, tmp_path):
        unknown_file = tmp_path / "test.xyz123"
        unknown_file.write_text("data")
        mime, cls = ClassificationEngine.detect_by_extension(unknown_file)
        assert cls == Classification.UNKNOWN

    def test_detect_by_magic_png(self, tmp_path):
        png_file = tmp_path / "test.bin"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 56)
        mime, cls = ClassificationEngine.detect_by_magic(png_file)
        assert cls == Classification.IMAGES
        assert mime == "image/png"

    def test_detect_by_magic_pdf(self, tmp_path):
        pdf_file = tmp_path / "test.bin"
        pdf_file.write_bytes(b"%PDF-1.5" + b"\x00" * 56)
        mime, cls = ClassificationEngine.detect_by_magic(pdf_file)
        assert cls == Classification.DOCUMENTS

    def test_detect_by_magic_no_match(self, tmp_path):
        txt_file = tmp_path / "test.bin"
        txt_file.write_bytes(b"Just plain text content here" + b"\x00" * 36)
        mime, cls = ClassificationEngine.detect_by_magic(txt_file)
        assert mime is None
        assert cls is None

    def test_classify_python_file(self, tmp_path):
        py_file = tmp_path / "script.py"
        py_file.write_text("#!/usr/bin/env python3\nprint('hi')")
        cls, mime, sens = ClassificationEngine.classify(py_file)
        assert cls == Classification.CODE

    def test_classify_env_file_sensitivity(self, tmp_path):
        env_file = tmp_path / "app.env"
        env_file.write_text("SECRET=value")
        cls, mime, sens = ClassificationEngine.classify(env_file)
        assert cls == Classification.CONFIGS
        assert sens == Sensitivity.CONFIDENTIAL

    def test_classify_key_file_sensitivity(self, tmp_path):
        key_file = tmp_path / "server.key"
        key_file.write_text("-----BEGIN PRIVATE KEY-----\ndata\n-----END PRIVATE KEY-----")
        cls, mime, sens = ClassificationEngine.classify(key_file)
        assert cls == Classification.CRYPTO
        assert sens == Sensitivity.TOP_SECRET

    def test_classify_pem_file(self, tmp_path):
        pem_file = tmp_path / "cert.pem"
        pem_file.write_text("cert data")
        cls, mime, sens = ClassificationEngine.classify(pem_file)
        assert cls == Classification.CRYPTO
        assert sens == Sensitivity.TOP_SECRET

    def test_scan_sensitive_content_email(self, tmp_path):
        text_file = tmp_path / "test.txt"
        text_file.write_text("Contact us at admin@example.com for info.")
        findings = ClassificationEngine.scan_sensitive_content(text_file)
        email_findings = [f for f in findings if f.pattern_name == "email"]
        assert len(email_findings) > 0

    def test_scan_sensitive_content_api_key(self, tmp_path):
        text_file = tmp_path / "config.txt"
        text_file.write_text('api_key = "sk_live_abcdefghijklmnopqrst1234567890"')
        findings = ClassificationEngine.scan_sensitive_content(text_file)
        key_findings = [f for f in findings if f.pattern_name == "api_key"]
        assert len(key_findings) > 0

    def test_scan_sensitive_content_private_key(self, tmp_path):
        text_file = tmp_path / "key.txt"
        pk_content = "-----BEGIN RSA PRIVATE KEY-----\nbase64data\n-----END RSA PRIVATE KEY-----"
        text_file.write_text(pk_content)
        findings = ClassificationEngine.scan_sensitive_content(text_file)
        pk_findings = [f for f in findings if f.pattern_name == "private_key"]
        assert len(pk_findings) > 0

    def test_scan_sensitive_no_findings(self, tmp_path):
        text_file = tmp_path / "safe.txt"
        text_file.write_text("This is a completely safe document with no sensitive data.")
        findings = ClassificationEngine.scan_sensitive_content(text_file)
        # Filter out low-risk patterns like IP addresses
        high_risk = [f for f in findings if f.risk_score >= 0.3]
        assert len(high_risk) == 0

    def test_redact_sample_short(self):
        assert ClassificationEngine._redact_sample("abc", 4) == "***"

    def test_redact_sample_long(self):
        result = ClassificationEngine._redact_sample("1234567890", 4)
        assert result.startswith("1234")
        assert result.endswith("7890")
        assert "*" in result


class TestSanitizationEngine:
    """Test SanitizationEngine."""

    def test_scan_sensitive_patterns(self):
        text = "Contact: test@example.com\nAPI_KEY=sk_live_1234567890abcdefghij"
        findings = SanitizationEngine.scan_sensitive_patterns(text)
        assert len(findings) > 0
        names = [f.pattern_name for f in findings]
        assert "email" in names

    def test_scan_sensitive_patterns_clean_text(self):
        text = "This is a normal paragraph with no sensitive information."
        findings = SanitizationEngine.scan_sensitive_patterns(text)
        high_risk = [f for f in findings if f.risk_score >= 0.3]
        assert len(high_risk) == 0


class TestDAGExecutor:
    """Test DAGExecutor task scheduling."""

    def test_add_task(self):
        executor = DAGExecutor(max_workers=2)
        task = DAGTask(task_id="t1", name="test", func=lambda **kw: "ok")
        executor.add_task(task)
        assert "t1" in executor.tasks

    def test_get_ready_tasks_no_deps(self):
        executor = DAGExecutor()
        t1 = DAGTask(task_id="t1", name="task1", func=lambda **kw: None)
        t2 = DAGTask(task_id="t2", name="task2", func=lambda **kw: None)
        executor.add_task(t1)
        executor.add_task(t2)
        ready = executor.get_ready_tasks()
        assert len(ready) == 2

    def test_get_ready_tasks_with_deps(self):
        executor = DAGExecutor()
        t1 = DAGTask(task_id="t1", name="task1", func=lambda **kw: None)
        t2 = DAGTask(
            task_id="t2", name="task2",
            func=lambda **kw: None,
            dependencies=["t1"],
        )
        executor.add_task(t1)
        executor.add_task(t2)
        ready = executor.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "t1"

    def test_get_ready_tasks_dep_completed(self):
        executor = DAGExecutor()
        t1 = DAGTask(task_id="t1", name="task1", func=lambda **kw: None)
        t1.status = TaskStatus.COMPLETED
        t2 = DAGTask(
            task_id="t2", name="task2",
            func=lambda **kw: None,
            dependencies=["t1"],
        )
        executor.add_task(t1)
        executor.add_task(t2)
        ready = executor.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "t2"

    def test_execute_task_success(self):
        executor = DAGExecutor()
        task = DAGTask(
            task_id="t1", name="test",
            func=lambda dep_results=None: 42,
        )
        executor.add_task(task)
        result = executor.execute_task(task)
        assert result is True
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 42
        assert task.duration > 0

    def test_execute_task_failure(self):
        def failing_func(**kw):
            raise ValueError("boom")

        executor = DAGExecutor()
        task = DAGTask(
            task_id="t1", name="failing",
            func=failing_func,
            max_retries=1,
        )
        executor.add_task(task)
        result = executor.execute_task(task)
        assert result is False
        assert task.error == "boom"
        assert task.status == TaskStatus.FAILED

    def test_execute_task_retry(self):
        def failing_func(**kw):
            raise ValueError("retry me")

        executor = DAGExecutor()
        task = DAGTask(
            task_id="t1", name="retry",
            func=failing_func,
            max_retries=3,
        )
        executor.add_task(task)
        executor.execute_task(task)
        # After first failure with retries remaining, status goes back to PENDING
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 1

    def test_execute_all_simple(self):
        executor = DAGExecutor(max_workers=2)
        t1 = DAGTask(
            task_id="t1", name="task1",
            func=lambda dep_results=None: "result1",
        )
        t2 = DAGTask(
            task_id="t2", name="task2",
            func=lambda dep_results=None: "result2",
        )
        executor.add_task(t1)
        executor.add_task(t2)
        results = executor.execute_all()
        assert results["total_tasks"] == 2
        assert results["completed"] == 2
        assert results["failed"] == 0

    def test_execute_all_with_deps(self):
        executor = DAGExecutor(max_workers=2)
        t1 = DAGTask(
            task_id="t1", name="first",
            func=lambda dep_results=None: "first_done",
        )
        t2 = DAGTask(
            task_id="t2", name="second",
            func=lambda dep_results=None: "second_done",
            dependencies=["t1"],
        )
        executor.add_task(t1)
        executor.add_task(t2)
        results = executor.execute_all()
        assert results["completed"] == 2
        assert results["duration"] > 0


class TestPhantomLogger:
    """Test PhantomLogger."""

    def test_logger_creation(self):
        log = PhantomLogger("test", verbose=False)
        assert log.name == "test"
        assert log.verbose is False

    def test_logger_format(self):
        log = PhantomLogger("test", verbose=False)
        console, file_msg = log._format("INFO", "Test message")
        assert "Test message" in file_msg
        assert "INFO" in file_msg

    def test_logger_audit_trail(self):
        log = PhantomLogger("test", verbose=False)
        log.audit("Test audit event")
        assert len(log.audit_log) == 1
        assert "Test audit event" in log.audit_log[0]["message"]

    def test_logger_methods(self):
        log = PhantomLogger("test", verbose=False)
        # These should not raise
        log.debug("debug msg")
        log.info("info msg")
        log.warning("warning msg")
        log.error("error msg")
        log.critical("critical msg")
        log.success("success msg")

    def test_logger_with_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        log = PhantomLogger("test", log_file=log_file, verbose=False)
        log.info("File log test")
        log.close()
        content = log_file.read_text()
        assert "File log test" in content


class TestPipelineContext:
    """Test PipelineContext dataclass."""

    def test_construction(self, tmp_path):
        ctx = PipelineContext(
            input_dir=tmp_path / "input",
            output_dir=tmp_path / "output",
            staging_dir=tmp_path / "staging",
            quarantine_dir=tmp_path / "quarantine",
        )
        assert ctx.workers == 4
        assert ctx.dry_run is False
        assert ctx.total_files == 0
        assert ctx.processed == 0


class TestSanitizationEnginePII:
    """Test SanitizationEngine PII redaction."""

    def test_sanitize_text_pii(self, tmp_path):
        src = tmp_path / "input.txt"
        dst = tmp_path / "output.txt"
        src.write_text("Email: admin@example.com and key: sk_live_ABCDEFGHIJKLMNO12345678")
        findings = [
            SensitiveFinding(
                pattern_type="regex",
                pattern_name="email",
                count=1,
                risk_score=0.8,
            ),
        ]
        result = SanitizationEngine.sanitize_text_pii(src, dst, findings)
        assert result is True
        content = dst.read_text()
        assert "admin@example.com" not in content
        assert "[REDACTED:email]" in content

    def test_sanitize_text_pii_low_risk_not_redacted(self, tmp_path):
        src = tmp_path / "input.txt"
        dst = tmp_path / "output.txt"
        src.write_text("IP address: 192.168.1.1")
        findings = [
            SensitiveFinding(
                pattern_type="regex",
                pattern_name="ip_address",
                count=1,
                risk_score=0.2,  # Below 0.7 threshold
            ),
        ]
        result = SanitizationEngine.sanitize_text_pii(src, dst, findings)
        assert result is True
        content = dst.read_text()
        # Low risk findings should NOT be redacted
        assert "192.168.1.1" in content


class TestClassificationEngineExtended:
    """Additional ClassificationEngine tests for coverage."""

    def test_detect_by_extension_image(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_text("fake image")
        mime, cls = ClassificationEngine.detect_by_extension(img)
        assert cls == Classification.IMAGES

    def test_detect_by_extension_archive(self, tmp_path):
        arc = tmp_path / "archive.zip"
        arc.write_text("fake zip")
        mime, cls = ClassificationEngine.detect_by_extension(arc)
        assert cls == Classification.ARCHIVES

    def test_classify_image_file(self, tmp_path):
        img = tmp_path / "photo.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 56)
        cls, mime, sens = ClassificationEngine.classify(img)
        assert cls == Classification.IMAGES

    def test_detect_by_magic_elf(self, tmp_path):
        elf = tmp_path / "binary"
        elf.write_bytes(b"\x7fELF" + b"\x00" * 60)
        mime, cls = ClassificationEngine.detect_by_magic(elf)
        assert cls == Classification.EXECUTABLES
        assert mime == "application/x-elf"

    def test_detect_by_magic_zip(self, tmp_path):
        zipf = tmp_path / "archive.bin"
        zipf.write_bytes(b"PK\x03\x04" + b"\x00" * 60)
        mime, cls = ClassificationEngine.detect_by_magic(zipf)
        assert cls == Classification.ARCHIVES

    def test_detect_by_magic_sqlite(self, tmp_path):
        db = tmp_path / "test.bin"
        db.write_bytes(b"SQLite format 3\x00" + b"\x00" * 48)
        mime, cls = ClassificationEngine.detect_by_magic(db)
        assert cls == Classification.DATA
        assert mime == "application/x-sqlite3"

    def test_detect_by_magic_shebang(self, tmp_path):
        script = tmp_path / "script.bin"
        script.write_bytes(b"#!/usr/bin/env python3\nprint('hello')\n" + b"\x00" * 30)
        mime, cls = ClassificationEngine.detect_by_magic(script)
        assert cls == Classification.CODE
        assert "script" in mime

    def test_scan_ip_address(self, tmp_path):
        cfg = tmp_path / "config.txt"
        cfg.write_text("server = 10.0.0.1\nbackup = 192.168.1.100")
        findings = ClassificationEngine.scan_sensitive_content(cfg)
        ip_findings = [fd for fd in findings if fd.pattern_name == "ipv4"]
        assert len(ip_findings) > 0


class TestDAGExecutorExtended:
    """Additional DAG executor tests."""

    def test_execute_all_with_failed_dep(self):
        """Task blocked by a failed dependency should not run."""
        def fail_func(**kw):
            raise ValueError("fail")

        executor = DAGExecutor(max_workers=1)
        t1 = DAGTask(
            task_id="t1", name="failing",
            func=fail_func, max_retries=0,
        )
        t2 = DAGTask(
            task_id="t2", name="blocked",
            func=lambda dep_results=None: "done",
            dependencies=["t1"],
        )
        executor.add_task(t1)
        executor.add_task(t2)
        results = executor.execute_all()
        assert results["failed"] >= 1

    def test_execute_all_empty_dag(self):
        executor = DAGExecutor()
        results = executor.execute_all()
        assert results["total_tasks"] == 0
        assert results["completed"] == 0
