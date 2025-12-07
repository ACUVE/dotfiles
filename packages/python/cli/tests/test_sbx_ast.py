"""Tests for sbx_ast module."""

import pytest
from cli.sbx import default_profile
from cli.sbx_ast import Integer, SExpression, String, Symbol
from cli.sbx_parser import parse


@pytest.fixture
def full_profile():
    """Fixture providing the complete sandbox profile for testing."""
    return """(version 1)

(allow default)

(import "system.sb")

(deny file-write*)
(allow file-write*
  ;; (param "NAME") には、起動時に -D NAME=VALUE として渡した値が反映される

  ;; プロジェクトディレクトリを TARGET_DIR として指定する
  (subpath (param "TARGET_DIR"))

  ;; git worktree を使っている場合に、御本尊の .git への書き込みを許可する (commit などできるように)
  (subpath (param "DOT_GIT_DIR"))

  ;; プロジェクトディレクトリ以外に書き込みを許可する場所
  ;; Claude Code関係
  (regex (string-append "^" (param "CLAUDE_CONFIG_DIR") "*"))
  (regex (string-append "^" (param "HOME_DIR") "/.claude*"))
  ;; セッション情報をKeychain経由で記録するらしい
  (subpath (string-append (param "HOME_DIR") "/Library/Keychains"))

  ;; 一時ファイル関連
  (subpath "/private/tmp")
  (subpath "/private/var/tmp")
  (subpath "/private/var/folders")
  (subpath (string-append (param "HOME_DIR") "/.cache"))
  (subpath (string-append (param "HOME_DIR") "/Library/Caches"))
  (subpath (string-append (param "HOME_DIR") "/.local/share"))

  (subpath (string-append (param "HOME_DIR") "/.npm"))
  (subpath (string-append (param "HOME_DIR") "/.pnpm"))
  (subpath (string-append (param "HOME_DIR") "/.yarn"))
  (subpath (string-append (param "HOME_DIR") "/.serena"))

  (subpath (string-append (param "HOME_DIR") "/.codex"))

  ;; STDOUTとか
  (literal "/dev/stdout")
  (literal "/dev/stderr")
  (literal "/dev/null")
  (literal "/dev/ptmx")
  (literal "/dev/dtracehelper")
  ;; /dev/ttys000 のようなパターンも許可したいためこのように書いています
  ;; regexとglobを混同しているように見えますが、なんか本当にこう書く必要があるらしく……
  (regex #"^/dev/tty*")
)

;; --- 禁止: node_modules とロックファイルへの書き込みを全域で拒否 ---
(deny file-write*
  ;; どのディレクトリ配下でも node_modules/ そのもの/配下を拒否
  ;; (regex #".*/node_modules(/|$)")
  ;; (regex #".*/.venv(/|$)")

  ;; ロックファイル（場所を問わずファイル名で拒否）
  ;; (regex #".*/package-lock\\.json$")
  ;; (regex #".*/pnpm-lock\\.yaml$")
  ;; (regex #".*/yarn\\.lock$")
  ;; (regex #".*/uv\\.lock$")
  ;; (regex #".*/poetry\\.lock$")

  ;; .env
  (regex #".*/\\.env$")
  ;; (regex #".*/\\.env\\..*$")
)

(allow file-write*
  ;; vitestが使うので許可
  (regex #".*/node_modules/\\.vite-temp(/|$)")
)

;; --- 機密ファイルの"内容読み取り"を禁止 (statは可) ---
(deny file-read-data
  (literal (string-append (param "HOME_DIR") "/.aws/credentials"))
  (literal (string-append (param "HOME_DIR") "/.zsh_history"))
  (literal (string-append (param "HOME_DIR") "/.bash_history"))
)

;; Keychain 解錠や設定参照など
(allow mach-lookup
  (global-name "com.apple.securityd")
  (global-name "com.apple.cfprefsd.xpc.agent")
  (global-name "com.apple.cfprefsd.xpc.daemon")
  (global-name "com.apple.ocspd")
  (global-name "com.apple.notifyd")
  (global-name "com.apple.SystemConfiguration.DNSConfiguration")
  (global-name "com.apple.coreservices.launchservicesd")
)

(allow ipc-posix-shm*
  (ipc-posix-name "com.apple.AppleDatabaseChanged")
)
"""


class TestASTNodes:
    """Test AST node classes."""

    def test_symbol_creation_and_string(self):
        """Test Symbol node creation and string conversion."""
        sym = Symbol("allow")
        assert sym.to_string() == "allow"
        assert str(sym) == "allow"

    def test_symbol_equality(self):
        """Test Symbol equality."""
        sym1 = Symbol("allow")
        sym2 = Symbol("allow")
        sym3 = Symbol("deny")
        assert sym1 == sym2
        assert sym1 != sym3

    def test_string_creation_and_string(self):
        """Test String node creation and string conversion."""
        s = String("hello world")
        assert s.to_string() == '"hello world"'
        assert str(s) == '"hello world"'

    def test_string_escaping(self):
        """Test String node escaping special characters."""
        s = String('test\n"quote"\\backslash')
        assert s.to_string() == '"test\\n\\"quote\\"\\\\backslash"'

    def test_string_equality(self):
        """Test String equality."""
        s1 = String("test")
        s2 = String("test")
        s3 = String("other")
        assert s1 == s2
        assert s1 != s3

    def test_integer_creation_and_string(self):
        """Test Integer node creation and string conversion."""
        i = Integer(42)
        assert i.to_string() == "42"
        assert str(i) == "42"

    def test_integer_equality(self):
        """Test Integer equality."""
        i1 = Integer(42)
        i2 = Integer(42)
        i3 = Integer(0)
        assert i1 == i2
        assert i1 != i3

    def test_sexpression_empty(self):
        """Test empty S-expression."""
        sexpr = SExpression([])
        assert sexpr.to_string() == "()"

    def test_sexpression_simple(self):
        """Test simple S-expression."""
        sexpr = SExpression([Symbol("allow"), Symbol("default")])
        assert sexpr.to_string() == "(allow default)"

    def test_sexpression_nested(self):
        """Test nested S-expression."""
        inner = SExpression([Symbol("literal"), String("/dev/null")])
        outer = SExpression([Symbol("allow"), Symbol("file-write*"), inner])
        result = outer.to_string()
        assert result.startswith("(allow")
        assert "/dev/null" in result

    def test_sexpression_equality(self):
        """Test S-expression equality."""
        sexpr1 = SExpression([Symbol("allow"), Symbol("default")])
        sexpr2 = SExpression([Symbol("allow"), Symbol("default")])
        sexpr3 = SExpression([Symbol("deny"), Symbol("default")])
        assert sexpr1 == sexpr2
        assert sexpr1 != sexpr3


class TestParser:
    """Test parser functionality."""

    def test_parse_simple_symbol(self):
        """Test parsing a simple symbol."""
        nodes = parse("allow")
        assert len(nodes) == 1
        assert isinstance(nodes[0], Symbol)
        assert nodes[0].name == "allow"

    def test_parse_string(self):
        """Test parsing a string."""
        nodes = parse('"hello world"')
        assert len(nodes) == 1
        assert isinstance(nodes[0], String)
        assert nodes[0].value == "hello world"

    def test_parse_integer(self):
        """Test parsing an integer."""
        nodes = parse("42")
        assert len(nodes) == 1
        assert isinstance(nodes[0], Integer)
        assert nodes[0].value == 42

    def test_parse_simple_sexpression(self):
        """Test parsing a simple S-expression."""
        nodes = parse("(allow default)")
        assert len(nodes) == 1
        assert isinstance(nodes[0], SExpression)
        assert len(nodes[0].elements) == 2
        assert nodes[0].elements[0] == Symbol("allow")
        assert nodes[0].elements[1] == Symbol("default")

    def test_parse_nested_sexpression(self):
        """Test parsing nested S-expressions."""
        nodes = parse("(allow file-write* (literal /dev/null))")
        assert len(nodes) == 1
        assert isinstance(nodes[0], SExpression)
        assert len(nodes[0].elements) == 3
        assert isinstance(nodes[0].elements[2], SExpression)

    def test_parse_with_comments(self):
        """Test parsing with comments."""
        nodes = parse("""
        ; This is a comment
        (allow default)
        ; Another comment
        """)
        assert len(nodes) == 1
        assert isinstance(nodes[0], SExpression)

    def test_parse_multiline(self):
        """Test parsing multiline expressions."""
        nodes = parse("""
        (version 1)
        (allow default)
        """)
        assert len(nodes) == 2
        assert isinstance(nodes[0], SExpression)
        assert nodes[0].elements[0] == Symbol("version")
        assert isinstance(nodes[1], SExpression)
        assert nodes[1].elements[0] == Symbol("allow")


class TestProfileParsing:
    """Test parsing the actual sandbox profile from sbx.py."""

    def test_parse_full_profile(self, full_profile):
        """Test parsing the complete profile from sbx.py."""
        nodes = parse(full_profile)

        # Verify we got multiple top-level expressions
        assert len(nodes) > 5

        # Check first expression is (version 1)
        assert isinstance(nodes[0], SExpression)
        assert nodes[0].elements[0] == Symbol("version")
        assert nodes[0].elements[1] == Integer(1)

        # Check second expression is (allow default)
        assert isinstance(nodes[1], SExpression)
        assert nodes[1].elements[0] == Symbol("allow")
        assert nodes[1].elements[1] == Symbol("default")

        # Check import statement
        assert isinstance(nodes[2], SExpression)
        assert nodes[2].elements[0] == Symbol("import")
        assert nodes[2].elements[1] == String("system.sb")

        # Verify deny and allow expressions exist
        deny_found = False
        allow_found = False
        for node in nodes:
            if isinstance(node, SExpression):
                if node.elements and node.elements[0] == Symbol("deny"):
                    deny_found = True
                if node.elements and node.elements[0] == Symbol("allow"):
                    allow_found = True

        assert deny_found, "No deny expressions found"
        assert allow_found, "No allow expressions found"

    def test_roundtrip_simple_expression(self):
        """Test that parsing and stringifying produces valid syntax."""
        original = "(allow file-write* (literal /dev/null))"
        nodes = parse(original)
        assert len(nodes) == 1

        # Reconstruct and parse again
        reconstructed = nodes[0].to_string()
        nodes2 = parse(reconstructed)

        # Should be equivalent
        assert nodes[0] == nodes2[0]

    def test_roundtrip_full_profile(self, full_profile):
        """Test that the full profile can be parsed, stringified, and re-parsed consistently."""
        # First parse
        nodes1 = parse(full_profile)
        assert len(nodes1) > 0, "Profile should parse into nodes"

        # Stringify all nodes
        stringified1 = "\n\n".join(node.to_string() for node in nodes1)

        # Second parse
        nodes2 = parse(stringified1)
        assert len(nodes2) == len(nodes1), (
            "Number of nodes should match after first round-trip"
        )

        # Stringify again
        stringified2 = "\n\n".join(node.to_string() for node in nodes2)

        # The second stringification should match the first
        assert stringified1 == stringified2, (
            "Stringified output should be stable after round-trip"
        )

        # Verify structural equivalence
        for n1, n2 in zip(nodes1, nodes2):
            assert n1 == n2, "Nodes should be structurally equivalent after round-trip"


class TestDefaultProfile:
    """Test that the default profile from sbx.py can be parsed."""

    def test_default_profile_parsing(self):
        """Test parsing the default profile from sbx.py."""
        profile = default_profile()
        nodes = parse(profile)

        # Verify we got multiple top-level expressions
        assert len(nodes) > 0

        # Check first expression is (version 1)
        assert isinstance(nodes[0], SExpression)
        assert nodes[0].elements[0] == Symbol("version")
        assert nodes[0].elements[1] == Integer(1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
