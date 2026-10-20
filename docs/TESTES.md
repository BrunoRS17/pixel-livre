# Testes automatizados

## Preparação

Na raiz do projeto, com Python 3.11+ de 64 bits:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

`requirements-dev.txt` inclui as dependências da aplicação e acrescenta pytest, pytest-qt e pytest-cov. Não é necessário instalar esses complementos apenas para usar o aplicativo.

## Comandos úteis

```powershell
# Somente núcleo e preferências
.\.venv\Scripts\python.exe -m pytest -m "not ui"

# Somente integração da interface
.\.venv\Scripts\python.exe -m pytest -m ui

# Cenários de transparência e cancelamento
.\.venv\Scripts\python.exe -m pytest -k "transparency or cancel"

# Cobertura e relatórios para inspeção
.\.venv\Scripts\python.exe -m pytest --cov=pixel_livre --cov-report=term-missing --cov-report=html --cov-report=xml --junitxml=test-results.xml

# Mesmo limite adotado na CI
.\.venv\Scripts\python.exe -m pytest --cov=pixel_livre --cov-fail-under=85
```

Abra `htmlcov/index.html` para visualizar o relatório HTML. Os relatórios e caches são ignorados pelo Git.

## Organização da suíte

| Arquivo | Comportamento verificado |
| --- | --- |
| `test_cleaner.py` | Remoção de campos PNG/EXIF, orientação em PNG/JPEG/WebP, transparência de paleta, fundo branco no JPEG, nomes exclusivos, rejeição de entrada inválida e limpeza de saídas parciais |
| `test_workflow.py` | Importação, duplicatas, diretórios inacessíveis, lote vazio, cancelamento antes/durante o lote e continuidade após erro |
| `test_settings.py` | Valores padrão, persistência de formato/pasta e recuperação de formato inválido |
| `test_ui.py` | Drop de arquivos/pastas, rejeição de URLs remotas, diálogo de saída, processamento real, restauração de controles, remoção da seleção e estado de erro |
| `conftest.py` | Fixtures compartilhadas e encerramento seguro de threads/widgets |
| `test_executable.py` | Binário independente, plugins Qt, codecs, interface, ZIP, arquitetura e checksums |

São **35 casos coletados** nesta versão, incluindo os casos parametrizados. O resultado local de referência foi 35 aprovados e 91% de cobertura combinada de linhas e ramificações, em Windows / Python 3.12.14 / PySide6 6.12.0 / pytest 9.1.1. Valores podem variar com versões e instrumentação de threads nativas.

Esse resultado é a referência da versão 0.2.0. Na 0.2.1 há mais três casos marcados `packaged`, executados quando `PIXEL_LIVRE_EXE` aponta para o binário gerado. Sem essa variável, esses três casos são ignorados explicitamente. Consulte [EMPACOTAMENTO.md](EMPACOTAMENTO.md) para gerar o executável e executar a bateria completa.

## Isolamento e decisões

- `tmp_path` cria um diretório exclusivo para cada teste; imagens são geradas pelo Pillow e não contêm dados pessoais.
- `image_factory` reduz repetição sem ocultar os dados relevantes de cada cenário.
- `preferences` injeta QSettings com arquivo INI temporário. O registro do usuário não é alterado.
- `window` registra a janela no qtbot e aguarda o encerramento do worker antes do descarte, inclusive quando um teste falha.
- `qtbot.waitUntil` acompanha a conclusão pelo loop de eventos, com timeout, em vez de sleeps fixos.
- Diálogos nativos são substituídos com `monkeypatch`; a limpeza, gravação de imagens e execução do worker são reais.
- `pytest.mark.parametrize` testa formatos e preferências sem duplicar o mesmo corpo de teste.
- Os testes usam `QT_QPA_PLATFORM=offscreen` por padrão, definido antes de criar QApplication. Para depuração visual no Windows, defina `$env:QT_QPA_PLATFORM = 'windows'` antes de executar.
- O teste de drag usa a assinatura compatível com Qt 6.8–6.11. Apenas o aviso de depreciação desse construtor em Qt 6.12 é filtrado localmente; outros avisos continuam visíveis.

## Integração contínua

O workflow `Tests` executa em `windows-latest` com Python 3.11, 3.12 e 3.13. É disparado em pushes para `main`, pull requests ou execução manual. Cada combinação instala `requirements-dev.txt`, roda a suíte, exige 85% de cobertura e armazena JUnit/XML por 14 dias. O token tem somente `contents: read`.

Após essa matriz, o job `Windows executable` gera uma compilação x64 e roda os três testes do pacote. O código de diagnóstico empacotado é verificado por esses subprocessos; ele não entra na cobertura do processo principal.

O limite de cobertura deixa explícita uma proteção contra regressões de testes; não justifica escrever testes sem comportamento verificável só para aumentar o percentual. A execução de entrada (`application.py`) e alguns caminhos de integração com o sistema ainda têm cobertura limitada.

## Limitações e verificações manuais

Os eventos de drop enviados pelo Qt não substituem testar o gesto real no Explorador, permissões/elevacão do Windows, diferentes escalas de tela e diálogos nativos. Antes de distribuir, confira também o cancelamento de uma imagem grande e a abertura da pasta no sistema.

Os testes de metadados verificam campos conhecidos em arquivos sintéticos; não são uma auditoria de todos os formatos de procedência, assinaturas, esteganografia ou C2PA.

Se um ambiente restrito bloquear a pasta temporária padrão, execute com `--basetemp=.pytest-tmp`. Esse caminho é reservado a testes, ignorado pelo Git e **apagado pelo pytest antes da execução**; nunca use uma pasta com dados pessoais como `--basetemp`.

## Publicação de versões

1. Atualize `pixel_livre/__init__.py`, README e CHANGELOG para a versão planejada.
2. Execute a suíte com cobertura e revise as mudanças.
3. Publique o commit em `main` e aguarde a matriz do workflow `Tests` terminar com sucesso.
4. Crie a tag `vX.Y.Z` no commit validado e publique o GitHub Release com notas e limitações.
5. Confira que tag, release e código apontam para o mesmo commit. Os arquivos Source code são gerados pelo GitHub; um executável exigiria empacotamento e validação separados.
