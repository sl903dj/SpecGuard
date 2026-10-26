from pathlib import Path

import pytest
from pydantic import ValidationError

from specguard.artifacts.models import (
    ArtifactBundle,
    ArtifactProviderConfig,
    ArtifactSubject,
    ContextDocument,
)


def test_artifact_config_defaults_and_relative_root() -> None:
    config = ArtifactProviderConfig(provider="speckit")
    assert config.include_context is True
    assert config.root == "specs"
    with pytest.raises(ValidationError):
        ArtifactProviderConfig(provider="speckit", root="/tmp/specs")
    with pytest.raises(ValidationError):
        ArtifactProviderConfig(provider="speckit", root="../specs")


def test_subject_requires_absolute_directory_and_valid_source(tmp_path: Path) -> None:
    subject = ArtifactSubject(
        provider="speckit",
        subject_id="003-demo",
        directory=tmp_path.resolve(),
        selection_source="config",
    )
    assert subject.directory.is_absolute()
    with pytest.raises(ValidationError):
        subject.model_copy(update={"directory": Path("specs/demo")}).model_validate(
            subject.model_copy(update={"directory": Path("specs/demo")}).model_dump()
        )


def test_bundle_ids_are_unique_and_context_is_bounded(tmp_path: Path) -> None:
    subject = ArtifactSubject(
        provider="speckit",
        subject_id="demo",
        directory=tmp_path.resolve(),
        selection_source="config",
    )
    context = ContextDocument(kind="plan", path="specs/demo/plan.md", content="ok")
    bundle = ArtifactBundle(subject=subject, context_documents=[context])
    assert bundle.requirements == []
    with pytest.raises(ValidationError):
        ContextDocument(kind="plan", path="../plan.md", content="bad")
