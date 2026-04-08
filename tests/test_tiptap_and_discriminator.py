"""Unit tests for TipTap stripping and tool discriminator fallback."""

from noxus_sdk.resources.conversations import (
    ConversationSettings,
    ConversationTool,
    NoxusQaTool,
    WebResearchTool,
    _tiptap_to_text,
    _tool_discriminator,
)


class TestTipTapToText:
    def test_none_returns_none(self):
        assert _tiptap_to_text(None) is None

    def test_plain_string(self):
        assert _tiptap_to_text("hello") == "hello"

    def test_empty_string_returns_none(self):
        assert _tiptap_to_text("") is None

    def test_dict_with_text(self):
        assert _tiptap_to_text({"text": "hello"}) == "hello"

    def test_dict_empty_text_returns_none(self):
        assert _tiptap_to_text({"text": ""}) is None

    def test_dict_no_text_key_returns_none(self):
        assert _tiptap_to_text({"foo": "bar"}) is None

    def test_list_of_dicts(self):
        assert _tiptap_to_text([{"text": "hello "}, {"text": "world"}]) == "hello world"

    def test_empty_list_returns_none(self):
        assert _tiptap_to_text([]) is None

    def test_list_with_empty_texts_returns_none(self):
        assert _tiptap_to_text([{"text": ""}, {"text": ""}]) is None


class TestToolDiscriminator:
    def test_known_type_from_dict(self):
        assert _tool_discriminator({"type": "web_research"}) == "web_research"

    def test_unknown_type_from_dict(self):
        assert _tool_discriminator({"type": "brand_new_tool"}) == "_fallback"

    def test_missing_type_from_dict(self):
        assert _tool_discriminator({}) == "_fallback"

    def test_known_type_from_model(self):
        tool = WebResearchTool()
        assert _tool_discriminator(tool) == "web_research"

    def test_unknown_value(self):
        assert _tool_discriminator(42) == "_fallback"


class TestConversationToolTipTap:
    def test_extra_instructions_plain_string(self):
        tool = NoxusQaTool(extra_instructions="Do X")
        assert tool.extra_instructions == "Do X"

    def test_extra_instructions_tiptap_dict(self):
        tool = NoxusQaTool.model_validate(
            {"type": "noxus_qa", "extra_instructions": {"text": "Do X"}}
        )
        assert tool.extra_instructions == "Do X"

    def test_extra_instructions_tiptap_list(self):
        tool = NoxusQaTool.model_validate(
            {"type": "noxus_qa", "extra_instructions": [{"text": "Do "}, {"text": "X"}]}
        )
        assert tool.extra_instructions == "Do X"


class TestConversationSettingsTipTap:
    def test_persona_tiptap_dict(self):
        settings = ConversationSettings.model_validate(
            {
                "model": ["gpt-4o"],
                "temperature": 0.7,
                "tools": [],
                "persona": {"text": "A friendly bot"},
            }
        )
        assert settings.persona == "A friendly bot"

    def test_tone_tiptap_list(self):
        settings = ConversationSettings.model_validate(
            {
                "model": ["gpt-4o"],
                "temperature": 0.7,
                "tools": [],
                "tone": [{"text": "Professional"}],
            }
        )
        assert settings.tone == "Professional"


class TestToolFallback:
    def test_unknown_tool_type_falls_back(self):
        """Unknown tool types should deserialize to base ConversationTool."""
        settings = ConversationSettings.model_validate(
            {
                "model": ["gpt-4o"],
                "temperature": 0.7,
                "tools": [{"type": "future_tool_xyz", "enabled": True}],
            }
        )
        assert len(settings.tools) == 1
        tool = settings.tools[0]
        assert isinstance(tool, ConversationTool)
        assert tool.type == "future_tool_xyz"

    def test_unknown_tool_preserves_extra_fields(self):
        """Unknown tool types should keep extra fields via ConfigDict(extra='allow')."""
        settings = ConversationSettings.model_validate(
            {
                "model": ["gpt-4o"],
                "temperature": 0.7,
                "tools": [{"type": "future_tool_xyz", "enabled": True, "custom_field": 42}],
            }
        )
        tool = settings.tools[0]
        assert tool.custom_field == 42  # type: ignore[attr-defined]
