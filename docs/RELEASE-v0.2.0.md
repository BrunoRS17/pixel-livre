# Pixel Livre v0.2.0

Uma interface renovada para limpar metadados de imagens localmente, com arrastar e soltar, escolha da pasta de saída e originais preservados.

## Destaques

- Interface em PySide6 com área de importação, prévia e painel de exportação.
- Arrastar imagens e pastas locais, sem importar arquivos duplicados.
- Pasta de saída e formato lembrados entre sessões.
- Código organizado em núcleo de processamento, interface e configurações.
- 35 testes automatizados com pytest, pytest-qt e pytest-cov.
- 91% de cobertura combinada na validação local em Windows/Python 3.12.
- Integração contínua em Windows/Python 3.11, 3.12 e 3.13, exigindo pelo menos 85% de cobertura.
- Documentação de uso, arquitetura, testes e motivos de cada escolha de stack.

## Como instalar ou atualizar

Baixe **Source code (zip)** e extraia o conteúdo. Na pasta extraída, com Python 3.11+ de 64 bits:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Depois da instalação, também é possível abrir com `Iniciar.bat`. Quem já tem um ambiente virtual deve executar novamente a instalação de `requirements.txt` para receber a dependência da nova interface.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest --cov=pixel_livre --cov-report=term-missing
```

## Limitações

Esta distribuição contém código-fonte; **não inclui um executável independente**. A limpeza remove metadados embutidos conhecidos pela estratégia de recriação dos pixels, não textos ou marcas d'água visíveis. JPEG é recodificado; perfis de cor são removidos. Não é um validador C2PA nem garantia de anonimização. Imagens animadas e multipágina são rejeitadas.

Os testes de interface usam eventos Qt e execução offscreen. O gesto real no Explorador e a aparência em diferentes escalas de tela ainda exigem conferência manual.
