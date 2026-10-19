# Pixel Livre

**Seus pixels ficam. Os metadados vão.**

Pixel Livre é um aplicativo desktop em Python para remover metadados embutidos de imagens em lote. Com uma interface em português, permite selecionar arquivos, conferir uma prévia e salvar cópias limpas em poucos cliques, preservando os originais. Todo o processamento acontece localmente, sem enviar imagens para servidores.

## Recursos

- Seleção de várias imagens ou de uma pasta inteira.
- Prévia com dimensões e tamanho do arquivo.
- Remoção de EXIF, GPS, XMP e comentários embutidos por recriação dos pixels.
- Correção da orientação EXIF antes da limpeza.
- Exportação em PNG, JPEG ou WebP.
- Barra de progresso, resultado por arquivo e cancelamento do lote.
- Cópias com nomes exclusivos, sem sobrescrever os arquivos existentes.

## Instalação no Windows

### 1. Prepare o Python

Instale **Python 3.11 ou superior** pelo [site oficial do Python](https://www.python.org/downloads/windows/), incluindo **Tcl/Tk** e a opção de adicionar Python ao PATH.

### 2. Baixe o projeto

Nesta página do GitHub, clique em **Code → Download ZIP** e extraia a pasta. Abra um terminal dentro da pasta extraída, onde está o arquivo `requirements.txt`.

### 3. Instale a dependência

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se o comando `python` não for reconhecido, use `py` no primeiro comando. Não é necessário ativar o ambiente virtual.

### 4. Abra o aplicativo

Dê dois cliques em **Iniciar.bat** ou execute:

```powershell
.\.venv\Scripts\python.exe app.py
```

O iniciador usa preferencialmente o ambiente `.venv` do projeto. A distribuição contém código Python e requer a instalação acima; não inclui um executável independente. O fluxo de abertura da pasta de saída foi desenvolvido para Windows.

## Como usar

1. Clique em **Adicionar imagens** ou **Adicionar pasta** (sem incluir subpastas).
2. Selecione uma imagem na lista para ver a prévia. Use Ctrl ou Shift para selecionar várias e removê-las da lista.
3. Escolha a pasta de destino e o formato de saída.
4. Clique em **Limpar imagens** e acompanhe o resultado de cada arquivo.
5. Clique em **Abrir pasta de saída** para acessar as cópias.

As saídas recebem `_limpa` no nome e um número quando necessário. Nenhum arquivo existente é substituído. Cancelar mantém as cópias já salvas e aguarda a conclusão da imagem atual. Repetir a limpeza gera novas cópias de toda a lista. Se houver erro, selecione a imagem para ler os detalhes na lateral.

## Formatos e limites

- Entrada: PNG, JPEG, WebP, BMP e TIFF de uma única página/quadro.
- Saída PNG: preserva os pixels convertidos e a transparência, mas pode gerar arquivos maiores.
- Saída WebP: compressão sem perdas e transparência.
- Saída JPEG: qualidade 95, com recompressão e transparência substituída por branco.
- Aplica a orientação EXIF antes de remover os metadados.
- Recria os pixels em RGB/RGBA sem copiar EXIF, GPS, XMP, comentários ou perfil ICC. Imagens de alta profundidade são convertidas para 8 bits por canal; perfis de cor removidos podem alterar a aparência em visualizadores.
- Imagens animadas e TIFF com várias páginas são rejeitados para evitar perda silenciosa de quadros.
- Não remove marcas d’água, textos, informações visíveis nos pixels ou dados esteganográficos. Não é uma ferramenta de anonimização completa nem um validador de credenciais C2PA. A recriação não preserva as credenciais embutidas, mas não garante remover vínculos externos de procedência.

## Verificação

Com o ambiente instalado, execute:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes cobrem remoção de metadados, orientação, transparência, preservação do original, nomes exclusivos e rejeição de arquivos corrompidos ou animados.

## Estrutura

| Arquivo | Função |
| --- | --- |
| `app.py` | Interface desktop em Tkinter |
| `cleaner.py` | Processamento das imagens com Pillow |
| `Iniciar.bat` / `iniciar.ps1` | Inicialização no Windows |
| `requirements.txt` | Dependência do projeto |
| `tests/test_cleaner.py` | Testes automatizados |

## Problemas comuns

- **Python não encontrado:** reinstale Python com a opção PATH ou use `py` para criar o ambiente.
- **Pillow não encontrado:** execute novamente a instalação de `requirements.txt` usando o Python da `.venv`.
- **Tkinter não encontrado:** modifique a instalação do Python para incluir Tcl/Tk.
- **Não foi possível salvar:** escolha uma pasta em que seu usuário tenha permissão de escrita.
- **Imagem rejeitada:** selecione o arquivo na lista e leia o erro na lateral; animações e arquivos com várias páginas não são aceitos.

## Contribuições

Sugestões e relatos de problemas são bem-vindos nas Issues. Inclua a versão do Python, o formato da imagem e a mensagem de erro. Evite anexar imagens com dados pessoais; prefira um exemplo fictício que reproduza o problema.
