from typing import Any, Dict

from config.error_codes import ERROR_TABLE
from models.pipeline_error import PipelineError


def _normalize_text(value: Any, fallback: str = "N/A") -> str:
    text = "" if value is None else str(value).strip()
    return text or fallback


def _resolve_stage_label(error: PipelineError) -> str:
    stage = _normalize_text(getattr(error, "stage", None), fallback="UNKNOWN")
    substep = _normalize_text(getattr(error, "substep", None), fallback="")
    return f"{stage.upper()}.{substep.upper()}" if substep else stage.upper()


def _resolve_summary(error: PipelineError) -> str:
    spec = ERROR_TABLE.get(error.code)
    if spec and getattr(spec, "short_pt", None):
        return _normalize_text(spec.short_pt, fallback=error.message)
    return _normalize_text(error.message, fallback="Falha operacional")


def format_short(error: PipelineError) -> str:
    """Retorna mensagem curta em uma linha para exibição rápida."""
    code = _normalize_text(getattr(error, "code", None), fallback="UNKNOWN")
    stage_label = _resolve_stage_label(error)
    summary = _resolve_summary(error)
    return f"[{code}] {stage_label} {summary}"


def format_detailed(error: PipelineError) -> str:
    """Retorna mensagem detalhada em português para suporte operacional."""
    spec = ERROR_TABLE.get(error.code)
    severity_label = _normalize_text(
        getattr(error, "severity_label", None)
        or (getattr(spec, "severity_label", None) if spec else None)
        or getattr(error, "severity_level", None),
        fallback="N/A",
    )
    severity_level = _normalize_text(
        getattr(error, "severity_level", None)
        or (getattr(spec, "severity_level", None) if spec else None),
        fallback="N/A",
    )
    summary = _resolve_summary(error)

    expected = _normalize_text(getattr(error, "expected", None), fallback="N/A")
    found = _normalize_text(getattr(error, "found", None), fallback="N/A")
    disk_number = _normalize_text(getattr(error, "disk_number", None), fallback="N/A")
    drive_letter = _normalize_text(getattr(error, "drive_letter", None), fallback="N/A")
    operation_id = _normalize_text(getattr(error, "operation_id", None), fallback="N/A")

    lines = [
        f"Código: {_normalize_text(error.code, fallback='UNKNOWN')}",
        f"Stage: {_normalize_text(error.stage, fallback='UNKNOWN')}",
        f"Substep: {_normalize_text(getattr(error, 'substep', None), fallback='N/A')}",
        f"Resumo: {summary}",
        "Esperado vs Encontrado:",
        f"- Esperado: {expected}",
        f"- Encontrado: {found}",
        f"Disco: {disk_number}",
        f"Unidade: {drive_letter}",
        f"Operação: {operation_id}",
        f"Severidade: {severity_label} (nível {severity_level})",
    ]

    detailed_spec = _normalize_text(getattr(spec, "detailed_pt", None), fallback="") if spec else ""
    if detailed_spec and detailed_spec != "N/A":
        lines.append(f"Detalhe: {detailed_spec}")

    return "\n".join(lines)


def format_structured(error: PipelineError) -> Dict[str, Any]:
    """Retorna estrutura serializável para logging técnico."""
    spec = ERROR_TABLE.get(error.code)
    return {
        "error_code": getattr(error, "code", None),
        "stage": getattr(error, "stage", None),
        "substep": getattr(error, "substep", None),
        "severity_level": getattr(error, "severity_level", None)
        if getattr(error, "severity_level", None) is not None
        else (getattr(spec, "severity_level", None) if spec else None),
        "retryable": getattr(error, "retryable", None)
        if getattr(error, "retryable", None) is not None
        else (getattr(spec, "retryable", None) if spec else None),
        "expected": getattr(error, "expected", None),
        "found": getattr(error, "found", None),
        "disk_number": getattr(error, "disk_number", None),
        "drive_letter": getattr(error, "drive_letter", None),
        "operation_id": getattr(error, "operation_id", None),
        "timestamp": getattr(error, "timestamp", None),
    }
