# Pixel Livre v0.4.0 — Privacidade além dos metadados

Baixe **Pixel-Livre-0.4.0-windows-x64.zip**, use **Extrair Tudo** e abra **PixelLivre.exe**. Não é necessário instalar Python.

## Novidades

- **Ocultar informações visíveis:** selecione uma imagem, abra o editor e arraste para cobrir regiões com preto opaco. Use zoom, desfazer e limpar marcações para revisar o resultado.
- **Salvar cópia protegida:** exporta um PNG sem metadados, com as áreas marcadas substituídas nos pixels, preservando o original e evitando sobrescritas.
- **Raio-X da Privacidade:** consulte metadados por categoria, com explicações, em uma interface clara e consistente com o aplicativo.
- Leitura e exportação em segundo plano; processamento inteiramente local.

## Validação

**62 testes aprovados localmente, com 91,82% de cobertura do processo principal.** Suíte automatizada com testes do editor, coordenadas em diferentes escalas, orientação EXIF, transparência, erros e preservação dos originais. O próprio executável é testado sem Python no PATH, incluindo Raio-X e exportação de uma imagem com regiões ocultadas.

## Uso e limitações

As marcações são manuais: cubra a informação inteira, revise as bordas com zoom e compartilhe a cópia `_oculta.png`. As marcações não são persistidas ao fechar o editor. A exportação desta ferramenta é sempre PNG; imagens animadas ou com várias páginas não são suportadas.

A ausência de achados no Raio-X não garante anonimato. A análise não detecta automaticamente dados pessoais visíveis ou conteúdo oculto nos pixels.

Pacote Windows x64 sem assinatura digital de editor. O Windows pode mostrar um aviso. O ZIP inclui licenças de terceiros e o release fornece **SHA256SUMS.txt** para conferir a integridade.
