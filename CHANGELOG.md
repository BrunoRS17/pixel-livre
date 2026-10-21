# Histórico de mudanças

## 0.3.0 — 2026-10-21 (sem release publicado)

- Raio-X da Privacidade: análise local dos metadados da imagem selecionada, com categorias e explicações.
- Leitura em segundo plano, exibição literal de valores e indicação de análises incompletas.
- Testes de GPS, autoria, datas, dispositivo, comparação após limpeza e integração da interface.
- Visual do Raio-X alinhado ao tema claro do aplicativo, inclusive no Windows com tema escuro.
- Executável atualizado e teste do diálogo de privacidade no próprio pacote.

## 0.2.1 — 2026-10-20

- Pacote portátil Windows x64, com executável que inclui Python, Qt e Pillow.
- Build reproduzível pelo script `scripts/build_windows.py`, usando PyInstaller 6.22.3.
- Recursos de versão do Windows, licenças de terceiros, informações de build e SHA-256.
- Testes do próprio executável em pasta isolada e sem Python no PATH, usando plugins Qt offscreen e Windows.
- Validação automatizada de arquitetura, conteúdo do ZIP e checksums.
- Job de build/teste Windows no GitHub Actions.
- Instruções para usuários sem Python e documentação de empacotamento.

O pacote não é assinado digitalmente. O release 0.2.0 permanece disponível como distribuição anterior de código-fonte.

## 0.2.0 — 2026-10-19

### Novidades

- Nova interface em PySide6, com painéis de importação, prévia e exportação.
- Arrastar e soltar arquivos e pastas locais, com tratamento de nomes com espaços e acentos.
- Escolha e persistência da pasta de saída e do formato.
- Arquitetura modular: núcleo independente de Qt, componentes de interface, worker e preferências.
- Suíte pytest com 35 casos, fixtures isoladas, parametrização, integração Qt e relatórios de cobertura.
- Workflow GitHub Actions para Windows em Python 3.11, 3.12 e 3.13, com limite mínimo de cobertura de 85%.
- README com instalação, uso e justificativas de stack; documentação de arquitetura e testes.

### Preservado

- Originais intactos e nomes de saída exclusivos.
- Limpeza local em PNG, JPEG e WebP, com correção de orientação EXIF.
- Cancelamento cooperativo e resultados individuais por imagem.
- Importação compatível por `from cleaner import clean_image`.

### Atualização e limites

Reinstale as dependências com `python -m pip install -r requirements.txt` no ambiente virtual. Tkinter foi substituído por PySide6. Para contribuir, instale `requirements-dev.txt` e execute `python -m pytest`.

Release de código-fonte, sem executável independente. O suporte validado é Windows; a interface offscreen não substitui a conferência manual do gesto de arrastar no Explorador. Imagens animadas/multipágina são rejeitadas e a limpeza não remove textos ou marcas d'água visíveis.
