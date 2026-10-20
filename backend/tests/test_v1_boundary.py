"""v1 code must not be reachable from v2 modules (v1-cleanup)."""
import ast
from pathlib import Path

from app.main import app

APP = Path(__file__).resolve().parents[1] / 'app'

REMOVED = {('POST', '/train'), ('GET', '/train-status/{sid}'), ('POST', '/preprocess'), ('GET', '/preprocess-status/{sid}'),
           ('GET', '/sample/{sid}'), ('POST', '/cluster'), ('GET', '/cluster-status/{sid}'), ('POST', '/cluster-refine'),
           ('POST', '/embed'), ('GET', '/embed-status/{sid}'), ('POST', '/persona'), ('GET', '/persona-status/{sid}'),
           ('GET', '/sna-data/{sid}')}
KEPT = {('POST', '/chat'), ('POST', '/insight-chat'), ('POST', '/search'), ('GET', '/sessions'), ('GET', '/session/{sid}'),
        ('POST', '/save-session'), ('POST', '/prep/{sid}/run'), ('GET', '/health')}
V1_MODULES = ('app.services.preprocessing', 'app.services.training', 'app.services.clustering',
              'app.services.embedding', 'app.services.personas', 'app.context.compat',
              'app.routers.labeling', 'app.routers.training', 'app.routers.preprocessing',
              'app.routers.clustering', 'app.routers.embedding', 'app.routers.personas', 'app.routers.keywords')


def registered():
    # Included routers can be lazy; OpenAPI resolves their registered operations.
    return {(method.upper(), path) for path, operations in app.openapi()['paths'].items()
            for method in operations}


def test_v1_routes_removed_and_chat_kept():
    routes = registered()
    assert REMOVED & routes == set()
    assert KEPT <= routes


def test_app_imports_no_v1_module():
    offenders = {}
    for path in APP.rglob('*.py'):
        hits = sorted(m for m in imported_modules(path) for v1 in V1_MODULES if m == v1 or m.startswith(v1 + '.'))
        if hits:
            offenders[str(path.relative_to(APP))] = hits
    assert offenders == {}


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


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f'{node.module}.{alias.name}' for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def test_prep_package_has_no_nested_v1_import():
    offenders = {str(p.relative_to(APP)): sorted(m for m in imported_modules(p) if m.startswith('app.services.preprocessing'))
                 for p in (APP / 'prep').glob('*.py')}
    assert {k: v for k, v in offenders.items() if v} == {}
