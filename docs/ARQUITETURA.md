# Arquitetura do Pixel Livre

O projeto separa processamento de imagens e apresentação. O núcleo pode ser reutilizado por outra interface ou um comando de terminal sem importar Qt. A interface coordena o trabalho por sinais, sem executar o lote na thread dos widgets.

## Responsabilidades

- `application.py`: cria QApplication, aplica o tema e injeta Preferences em MainWindow.
- `core/cleaning.py`: transforma uma imagem e grava uma cópia com nome exclusivo. Mantém orientação, trata transparência e não transporta os metadados de origem.
- `core/importing.py`: normaliza caminhos, filtra extensões, remove duplicatas e expande somente o primeiro nível de pastas. ImportResult comunica arquivos aceitos, ignorados e erros.
- `core/batch.py`: executa sequencialmente as imagens; ImageResult e BatchSummary descrevem o resultado sem depender de widgets. Recebe callbacks e um threading.Event para cancelamento.
- `settings.py`: persiste apenas a pasta de destino e o formato via QSettings. Aceita armazenamento injetável para testes isolados.
- `ui/components.py`: componentes reutilizáveis, incluindo DropZone, que aceita apenas URLs de arquivos locais e emite caminhos decodificados pelo Qt.
- `ui/view.py`: constrói os painéis e controles, sem abrir arquivos ou executar limpeza.
- `ui/theme.py`: concentra cores, tipografia e estados visuais.
- `ui/window.py`: controlador da janela; mantém a seleção e conecta ações, preferências e processamento. Faz validação inicial do destino e apresenta erros.
- `ui/worker.py`: adaptador QThread para o serviço de lotes. Emite sinais; não acessa widgets.

## Fluxo

```text
Arrastar / selecionar → collect_images → lista e prévia
Escolher destino + formato → Preferences
Limpar → CleaningWorker → run_batch → clean_image
                           ↓ sinais
                    progresso e resultados
```

## Decisões importantes

- A seleção é congelada durante a execução. Nenhum índice de resultado muda enquanto um lote está em andamento.
- O cancelamento é cooperativo: termina a imagem atual, preserva as saídas concluídas e não inicia as seguintes.
- O fechamento é bloqueado durante o processamento. Os controles são liberados somente após o sinal `QThread.finished`, evitando destruir uma thread ativa.
- Os erros de leitura e gravação são isolados por imagem; os demais arquivos continuam sendo processados.
- O arquivo de saída é reservado com abertura exclusiva (`xb`), evitando sobrescritas mesmo quando nomes colidem. Falhas na codificação removem apenas a saída parcial criada pela operação.
- A prévia aplica orientação e limita suas dimensões. A decodificação da prévia ainda ocorre na thread de interface; imagens muito grandes podem causar uma pausa. Uma futura fila de miniaturas pode remover essa limitação.
- A pasta de saída pode ser escolhida por diálogo ou digitada. A criação efetiva ocorre no processamento e falhas de permissão aparecem no resultado.
- A interface usa PySide6 Essentials, suficiente para Qt Widgets, evitando exigir os módulos de navegador e multimídia.
- `cleaner.py` continua exportando a API anterior para compatibilidade; código novo importa o módulo em `core`.

## Testes e evolução

Instale `requirements-dev.txt` e execute `.\.venv\Scripts\python.exe -m pytest` na raiz. Os testes usam fixtures pytest, arquivos sintéticos e `tmp_path`. Os testes de interface usam pytest-qt para enviar eventos Qt de arrastar/soltar, exercitar a seleção de destino e processar um lote real, com configuração isolada. Veja [TESTES.md](TESTES.md) para detalhes e comandos de cobertura.

Para adicionar um novo formato, atualize o núcleo, os testes de metadados/transparência e a seleção da interface. Para mudar o visual, concentre as alterações em theme, components e view. Novos serviços devem retornar dados e resultados; diálogos e mensagens pertencem à apresentação.

Validação visual: janela padrão e tamanho mínimo (940 × 720), estado vazio, seleção, progresso e conclusão. O teste automatizado de drop valida o contrato de eventos Qt; o gesto real no Explorador também deve ser conferido em cada distribuição Windows.
