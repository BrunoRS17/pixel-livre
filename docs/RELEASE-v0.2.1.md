# Pixel Livre v0.2.1 — Windows sem Python

## Download

Baixe **Pixel-Livre-0.2.1-windows-x64.zip**, extraia com **Extrair Tudo** e abra **PixelLivre.exe**.

Não é necessário instalar Python, pip ou bibliotecas. O pacote é portátil, para Windows x64, e não precisa de administrador. A primeira abertura pode levar alguns segundos para extrair os componentes internos.

O ZIP contém o executável, instruções, informações de build e licenças de componentes de terceiros. Os arquivos **Source code** são destinados a quem quer desenvolver ou executar pelo Python.

## Novidades

- Executável independente com Python, Pillow e Qt incluídos.
- Build automatizado com PyInstaller e metadados de versão do Windows.
- Três testes adicionais do pacote: Qt offscreen, Qt Windows nativo, integridade do ZIP/checksums e arquitetura x64.
- Testes do executável em pasta isolada e sem Python no PATH.
- CI recompila e testa o pacote após a matriz de testes em Python 3.11, 3.12 e 3.13.
- README e guia de empacotamento atualizados.

Validação local: **38 testes aprovados**, incluindo os três testes do pacote, e **90% de cobertura** do código medido no processo pytest. O teste do executável roda separadamente e verifica a janela real, codecs e gravação de imagens.

## Integridade

Compare o hash do ZIP com o arquivo **SHA256SUMS.txt**:

```powershell
Get-FileHash .\Pixel-Livre-0.2.1-windows-x64.zip -Algorithm SHA256
```

## Limitações

O executável não possui assinatura digital de editor e pode receber avisos do Windows. Baixe apenas desta página oficial, confira o checksum e respeite as políticas de segurança do computador.

Validado localmente no Windows 11 e por testes no runner Windows do GitHub; não é uma compilação ARM64 ou de 32 bits. Testar sem Python no PATH não substitui uma matriz completa de máquinas Windows recém-instaladas.

A limpeza preserva os originais, mas não remove textos ou marcas d'água visíveis. JPEG é recodificado e perfis de cor são removidos. Credenciais C2PA e anonimização completa não são garantidas.
