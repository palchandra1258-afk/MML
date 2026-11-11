"""Conservative concept grounding from the local EdNet question metadata."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zipfile import ZipFile


_SKILL_ID = re.compile(r"^ednet_skill:(\d+)$")


@dataclass(frozen=True)
class ConceptGrounding:
    concept_id: str
    concept_name: str | None
    name_status: str
    source_dataset: str | None
    related_skill_ids: tuple[str, ...]
    related_question_ids: tuple[str, ...]
    related_lecture_ids: tuple[str, ...]
    lecture_parts: tuple[str, ...]
    lecture_video_length_values: tuple[str, ...]
    parts: tuple[str, ...]
    bundle_ids: tuple[str, ...]
    explanation_reference_ids: tuple[str, ...]
    learning_objective: str | None
    prerequisites: tuple[str, ...]
    example_ids: tuple[str, ...]
    representation_content_ids: tuple[str, ...]
    content_status: str
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        reference_limit = 20
        question_ids = list(self.related_question_ids)
        parts = list(self.parts)
        bundle_ids = list(self.bundle_ids)
        explanation_ids = list(self.explanation_reference_ids)
        lecture_ids = list(self.related_lecture_ids)
        lecture_parts = list(self.lecture_parts)
        lecture_lengths = list(self.lecture_video_length_values)
        return {
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "name_status": self.name_status,
            "source_dataset": self.source_dataset,
            "related_skill_ids": list(self.related_skill_ids),
            "related_question_ids": question_ids[:reference_limit],
            "related_question_id_count": len(question_ids),
            "related_question_ids_truncated": len(question_ids) > reference_limit,
            "related_lecture_ids": lecture_ids[:reference_limit],
            "related_lecture_id_count": len(lecture_ids),
            "related_lecture_ids_truncated": len(lecture_ids) > reference_limit,
            "lecture_parts": lecture_parts[:reference_limit],
            "lecture_part_count": len(lecture_parts),
            "lecture_parts_truncated": len(lecture_parts) > reference_limit,
            "lecture_video_length_values": lecture_lengths[:reference_limit],
            "lecture_video_length_count": len(lecture_lengths),
            "lecture_video_lengths_truncated": len(lecture_lengths) > reference_limit,
            "parts": parts[:reference_limit],
            "part_count": len(parts),
            "parts_truncated": len(parts) > reference_limit,
            "bundle_ids": bundle_ids[:reference_limit],
            "bundle_id_count": len(bundle_ids),
            "bundle_ids_truncated": len(bundle_ids) > reference_limit,
            "explanation_reference_ids": explanation_ids[:reference_limit],
            "explanation_reference_id_count": len(explanation_ids),
            "explanation_reference_ids_truncated": len(explanation_ids) > reference_limit,
            "learning_objective": self.learning_objective,
            "prerequisites": list(self.prerequisites),
            "example_ids": list(self.example_ids),
            "representation_content_ids": list(self.representation_content_ids),
            "content_status": self.content_status,
            "limitations": list(self.limitations),
        }


class EdNetContentCatalog:
    """Index tag/question metadata, excluding answer keys and learner records."""

    def __init__(self) -> None:
        self._by_skill: dict[str, list[dict[str, str | None]]] = {}
        self._lectures_by_skill: dict[str, dict[str, dict[str, str | None]]] = {}
        self._loaded_from: str | None = None

    @classmethod
    def from_zip(cls, archive_path: str | Path) -> "EdNetContentCatalog":
        path = Path(archive_path)
        catalog = cls()
        with ZipFile(path) as archive:
            member = next((name for name in archive.namelist() if name.endswith("contents/questions.csv")), None)
            if member is None:
                raise ValueError("EdNet content archive does not contain contents/questions.csv")
            with archive.open(member) as binary:
                import io

                text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
                reader = csv.DictReader(text)
                required = {"question_id", "tags"}
                if not required <= set(reader.fieldnames or []):
                    raise ValueError("question metadata is missing question_id or tags")
                for row in reader:
                    question_id = (row.get("question_id") or "").strip()
                    tags = (row.get("tags") or "").strip()
                    if not question_id or not tags or tags == "-1":
                        continue
                    metadata = {
                        "question_id": question_id,
                        "part": (row.get("part") or "").strip() or None,
                        "bundle_id": (row.get("bundle_id") or "").strip() or None,
                        "explanation_id": (row.get("explanation_id") or "").strip() or None,
                    }
                    for raw_tag in tags.split(";"):
                        tag = raw_tag.strip()
                        if tag.isdigit():
                            catalog._by_skill.setdefault(f"ednet_skill:{tag}", []).append(metadata)
            lecture_member = next((name for name in archive.namelist() if name.endswith("contents/lectures.csv")), None)
            if lecture_member is not None:
                with archive.open(lecture_member) as binary:
                    import io

                    reader = csv.DictReader(io.TextIOWrapper(binary, encoding="utf-8", newline=""))
                    if not {"lecture_id", "tags"} <= set(reader.fieldnames or []):
                        raise ValueError("lecture metadata is missing lecture_id or tags")
                    for row in reader:
                        lecture_id = (row.get("lecture_id") or "").strip()
                        tags = (row.get("tags") or "").strip()
                        if not lecture_id or not tags or tags == "-1":
                            continue
                        for raw_tag in tags.split(";"):
                            tag = raw_tag.strip()
                            if tag.isdigit():
                                catalog._lectures_by_skill.setdefault(f"ednet_skill:{tag}", {})[lecture_id] = {
                                    "lecture_id": lecture_id,
                                    "part": (row.get("part") or "").strip() or None,
                                    "video_length": (row.get("video_length") or "").strip() or None,
                                }
        catalog._loaded_from = f"{path}#{member}"
        return catalog

    def ground(self, concept_id: str) -> ConceptGrounding:
        match = _SKILL_ID.fullmatch(concept_id)
        if match is None:
            return ConceptGrounding(
                concept_id=concept_id,
                concept_name=None,
                name_status="unavailable",
                source_dataset=None,
                related_skill_ids=(),
                related_question_ids=(),
                related_lecture_ids=(),
                lecture_parts=(),
                lecture_video_length_values=(),
                related_question_id_count=0,
                related_question_ids_truncated=False,
                parts=(),
                part_count=0,
                parts_truncated=False,
                bundle_ids=(),
                bundle_id_count=0,
                bundle_ids_truncated=False,
                explanation_reference_ids=(),
                explanation_reference_id_count=0,
                explanation_reference_ids_truncated=False,
                learning_objective=None,
                prerequisites=(),
                example_ids=(),
                representation_content_ids=(),
                content_status="unavailable",
                limitations=("No local concept catalog maps this identifier to curriculum content.",),
            )
        rows = self._by_skill.get(concept_id, [])
        lecture_rows = list(self._lectures_by_skill.get(concept_id, {}).values())
        lecture_ids = sorted({str(row["lecture_id"]) for row in lecture_rows})
        if not rows and not lecture_ids:
            limitations = ("This EdNet skill tag is not present in the local question-content metadata.",)
        else:
            limitations = (
                "EdNet skill tags are item metadata; they do not provide validated concept names or learning objectives.",
                "Question, bundle, part, and explanation identifiers are references only; no worked examples or explanation content are available through this catalog.",
                "Lecture IDs/parts/tags in the archive are metadata references; the lecture video assets are not present in the inspected content archive.",
                "Prerequisite relationships are not present in the inspected metadata.",
            )
        return ConceptGrounding(
            concept_id=concept_id,
            concept_name=None,
            name_status="identifier_only" if rows or lecture_ids else "unavailable",
            source_dataset="EdNet-KT1" if rows or lecture_ids else None,
            related_skill_ids=(concept_id,) if rows or lecture_ids else (),
            related_question_ids=tuple(sorted({str(row["question_id"]) for row in rows})),
            related_lecture_ids=tuple(lecture_ids),
            parts=tuple(sorted(
                {str(row["part"]) for row in rows if row["part"]}
                | {str(row["part"]) for row in lecture_rows if row["part"]}
            )),
            bundle_ids=tuple(sorted({str(row["bundle_id"]) for row in rows if row["bundle_id"]})),
            explanation_reference_ids=tuple(sorted({str(row["explanation_id"]) for row in rows if row["explanation_id"]})),
            lecture_parts=tuple(sorted({str(row["part"]) for row in lecture_rows if row["part"]})),
            lecture_video_length_values=tuple(sorted({str(row["video_length"]) for row in lecture_rows if row["video_length"]})),
            learning_objective=None,
            prerequisites=(),
            example_ids=(),
            representation_content_ids=(),
            content_status="metadata_only" if rows or lecture_ids else "unavailable",
            limitations=limitations,
        )

    @property
    def source(self) -> str | None:
        return self._loaded_from
