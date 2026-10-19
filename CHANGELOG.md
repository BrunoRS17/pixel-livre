# Histórico de mudanças

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
