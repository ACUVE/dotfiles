"""Test that sbx.py profile generation matches expectations."""

import pytest
from cli.sbx import _build_profile
from cli.sbx_ast import Integer, Symbol, String


class TestSbxProfile:
    """Test sandbox profile building."""

    def test_build_profile_structure(self):
        """Test that _build_profile returns correct structure."""
        nodes = _build_profile()

        # Should have 10 top-level expressions
        assert len(nodes) == 10

        # First should be (version 1)
        assert len(nodes[0].elements) == 2
        assert isinstance(nodes[0].elements[0], Symbol)
        assert nodes[0].elements[0].name == "version"
        assert isinstance(nodes[0].elements[1], Integer)
        assert nodes[0].elements[1].value == 1

        # Second should be (allow default)
        assert len(nodes[1].elements) == 2
        assert isinstance(nodes[1].elements[0], Symbol)
        assert nodes[1].elements[0].name == "allow"
        assert isinstance(nodes[1].elements[1], Symbol)
        assert nodes[1].elements[1].name == "default"

        # Third should be (import "system.sb")
        assert len(nodes[2].elements) == 2
        assert isinstance(nodes[2].elements[0], Symbol)
        assert nodes[2].elements[0].name == "import"
        assert isinstance(nodes[2].elements[1], String)
        assert nodes[2].elements[1].value == "system.sb"

    def test_build_profile_to_string(self, full_profile):
        """Test that _build_profile generates the same profile as the fixture."""
        nodes = _build_profile()
        generated = "\n\n".join(node.to_string() for node in nodes)

        # The generated profile should be parseable and produce equivalent nodes
        from cli.sbx_parser import parse

        fixture_nodes = parse(full_profile)
        generated_nodes = parse(generated)

        # Both should have the same number of nodes
        assert len(fixture_nodes) == len(generated_nodes)

        # All nodes should be structurally equivalent
        for fixture_node, generated_node in zip(fixture_nodes, generated_nodes):
            assert fixture_node == generated_node

    def test_build_profile_equals_parsed_fixture(self, full_profile):
        """Test that _build_profile() directly equals parsed full_profile fixture."""
        from cli.sbx_parser import parse

        # Parse the fixture
        fixture_nodes = parse(full_profile)

        # Get the programmatically built profile
        built_nodes = _build_profile()

        # Should have the same number of nodes
        assert len(fixture_nodes) == len(built_nodes), (
            f"Number of nodes mismatch: fixture has {len(fixture_nodes)}, "
            f"built has {len(built_nodes)}"
        )

        # All nodes should be structurally equivalent
        for i, (fixture_node, built_node) in enumerate(zip(fixture_nodes, built_nodes)):
            assert fixture_node == built_node, (
                f"Node {i} mismatch:\n"
                f"Fixture: {fixture_node.to_string()}\n"
                f"Built:   {built_node.to_string()}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
