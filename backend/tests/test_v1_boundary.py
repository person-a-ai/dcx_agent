"""v1 code must not be reachable from v2 modules (v1-cleanup)."""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'app'


def top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    names = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f'{node.module}.{alias.name}' for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def test_prep_package_does_not_import_v1_preprocessing():
    offenders = {str(p.relative_to(APP)): sorted(m for m in top_level_imports(p) if m.startswith('app.services.preprocessing'))
                 for p in (APP / 'prep').glob('*.py')}
    assert {k: v for k, v in offenders.items() if v} == {}
