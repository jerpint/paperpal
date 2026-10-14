import json
from types import SimpleNamespace
import pytest
from paperpal import sources, cli, server

INDEX = '[Latest](years/2026.md#latest)'
ISSUE = '''# Archive
## Latest week
| 1) **Example** - curator summary | [Paper](https://academy.dair.ai/papers/example-2610.12345) |
| 2) **Duplicate** | [Paper](https://arxiv.org/abs/2610.12345v2) |
| 3) **Non-arxiv** | [Paper](https://example.org/article) |
## Older week
| 1) **Old** | [Paper](https://arxiv.org/abs/2501.12345) |
'''

def fake_feed(monkeypatch, index=INDEX, issue=ISSUE):
    calls = []
    def get(url):
        calls.append(url)
        return SimpleNamespace(text=index if url.endswith('README.md') else issue)
    monkeypatch.setattr(sources, '_get', get)
    return calls

def test_latest_dedup_and_primary_separation(monkeypatch):
    calls = fake_feed(monkeypatch)
    result = sources.dair_papers()
    assert len(calls) == 2
    assert len(result['papers']) == 1
    paper = result['papers'][0]
    assert paper['primary_url'] == 'https://arxiv.org/abs/2610.12345'
    assert paper['discovery_url'].startswith('https://academy.dair.ai/')
    assert paper['read_status'] == 'unread'
    assert result['issue'] == 'Latest week'

@pytest.mark.parametrize('index,issue', [('changed', ISSUE), (INDEX, '# empty'), (INDEX, '## Empty\nno papers')])
def test_format_changes_are_explicit(monkeypatch, index, issue):
    fake_feed(monkeypatch, index, issue)
    with pytest.raises(sources.SourceError):
        sources.dair_papers()

def test_cli_mcp_share_result(monkeypatch, capsys):
    fake_feed(monkeypatch)
    assert cli.main(['dair']) == 0
    cli_result = json.loads(capsys.readouterr().out)
    mcp_result = json.loads(server.dair_papers())
    assert cli_result['papers'] == mcp_result['papers']
