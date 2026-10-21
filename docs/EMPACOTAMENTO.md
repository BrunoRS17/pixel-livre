# Executável Windows

## Distribuição

O release v0.4.0 contém `Pixel-Livre-0.4.0-windows-x64.zip` e `SHA256SUMS.txt`. O ZIP inclui `PixelLivre.exe`, instruções, versões das dependências de build e licenças de terceiros. Extraia o ZIP e abra o executável. O usuário final não precisa instalar Python.

O arquivo é gerado com PyInstaller em modo `onefile` e `windowed`, sem UPX e sem elevação de administrador. Os módulos Python, DLLs do Qt/Pillow e o interpretador são extraídos temporariamente pelo bootloader. O build é específico para Windows x64; não é um instalador nem um pacote ARM64.

## Gerar em ambiente isolado

Em Windows x64, com Python x64:

```powershell
python -m venv .build-venv
.\.build-venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.build-venv\Scripts\python.exe scripts/build_windows.py
```

O script usa `packaging/PixelLivre.spec`, gera os recursos de versão do Windows a partir de `pixel_livre.__version__` e escreve os artefatos em `dist/`. O build inclui somente os módulos necessários para a aplicação; o ambiente de testes não precisa ser distribuído.

O processo de empacotamento recebe um PATH restrito ao ambiente Python e ao Windows. Isso evita incluir DLLs incompatíveis de outras ferramentas instaladas na máquina (por exemplo, bibliotecas ICU de outro programa). O cache do PyInstaller fica em `build/pyinstaller-cache` e é renovado durante a compilação.

PyInstaller está fixado em 6.22.3. As demais dependências seguem os intervalos de `requirements.txt`; `BUILD-INFO.txt` registra as versões usadas. Builds separados não são necessariamente idênticos byte a byte; compare o hash com o arquivo de checksums correspondente ao mesmo release.

## Testar o binário

Depois do build:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PIXEL_LIVRE_EXE = (Resolve-Path .\dist\PixelLivre.exe).Path
.\.venv\Scripts\python.exe -m pytest -m packaged
```

Os testes:

1. Copiam somente o executável para uma pasta temporária com espaços e acentos.
2. Removem `PYTHONHOME`, `PYTHONPATH`, `VIRTUAL_ENV` e caminhos de plugins Qt externos; restringem PATH ao System32.
3. Executam o arquivo empacotado, com `sys.frozen` confirmado, nos plugins Qt offscreen e Windows nativo.
4. Verificam gravação/leitura PNG, JPEG e WebP, remoção de campos sintéticos, transparência e preservação do original.
5. Abrem a janela real e exercitam prévia, exportação pelo worker e preferências isoladas.
6. Validam a arquitetura PE AMD64, licenças, conteúdo do ZIP e SHA-256 do executável/arquivo.

O modo interno `--self-test-dir CAMINHO` só é ativado explicitamente. Exige uma pasta nova para não sobrescrever dados; gera imagens sintéticas, INI, relatório JSON e captura da própria janela, depois encerra. A abertura normal não executa os testes nem cria esse relatório.

Os testes do pacote ficam fora da medição de cobertura do processo pytest: o binário roda em outro processo. `diagnostics.py` é omitido desse percentual e é validado pela execução do próprio pacote. A suíte funcional e de interface continua separada, com limite de 85% na CI.

## Validação e limites

Na validação local da v0.2.1, os **38 testes passaram** (35 funcionais/interface e três do pacote). A cobertura do processo principal foi **90%**. A captura gerada pelo binário confirmou a interface com uma imagem sintética exportada e resultado concluído.

O teste sem Python no PATH e fora do repositório verifica que o programa utiliza as dependências empacotadas; não equivale a testar todas as edições do Windows em uma máquina recém-instalada. O pacote foi validado localmente no Windows 11; o GitHub Actions também recompila e executa os testes em um runner Windows.

A interface usa o plugin nativo Windows na bateria de testes, mas diálogos do Explorador, gesto físico de drag-and-drop, SmartScreen, antivírus e diferentes escalas de tela ainda precisam de verificação específica quando houver mudanças nessas integrações.

O executável não tem assinatura digital de editor. Não desative proteções do Windows para executá-lo. Compare o SHA-256 com o release oficial; ambientes corporativos podem exigir aprovação ou assinatura antes de permitir execução.

## Publicar

Após a suíte funcional, o build local, os testes do pacote e os jobs de CI passarem:

- Crie uma tag correspondente ao commit validado.
- Publique um GitHub Release com as instruções de download.
- Anexe o ZIP e `SHA256SUMS.txt`; mantenha o executável fora do histórico Git.
- Verifique os tamanhos e hashes dos anexos publicados.

O job `Windows executable` mantém uma compilação independente nos artefatos de CI por 14 dias. A distribuição permanente fica nos anexos do release.

Na validação da v0.4.0, 62 testes passaram com 91,82% de cobertura do processo principal. O binário também abriu o Raio-X e exportou uma cópia PNG com região coberta, verificando os pixels e os metadados.
