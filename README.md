# Mapa estático de Petrópolis

Este diretório contém um mapa Folium/Leaflet que carrega quatro camadas GeoJSON locais e foi preparado para publicação direta no GitHub Pages.

## Estrutura

- `index.html` – mapa Leaflet já apontando para as camadas via caminhos relativos (`camadas/*.geojson`).
- `camadas/` – GeoJSONs necessários (`setores`, `drm2022`, `pmrr2017`, `vistorias`).
- `build_map.py` – script opcional para regenerar o `index.html` com Folium.
- `publish_github_pages.sh` – automatiza criação do repositório, push e configuração do GitHub Pages.

## Regerando o mapa

1. Crie um ambiente isolado (opcional mas recomendado):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install folium
   ```
2. Garanta que os GeoJSONs estejam dentro de `camadas/`.
3. Execute:
   ```bash
   python build_map.py
   ```
   O arquivo `index.html` será sobrescrito usando caminhos relativos para `camadas/`.

## Publicando no GitHub Pages

Pré-requisitos: `git` e [GitHub CLI](https://cli.github.com/) instalados e autenticados.

1. Ajuste o nome do repositório (opcional) passando como primeiro argumento. Exemplo:
   ```bash
   ./publish_github_pages.sh petropolis-map
   ```
   Se nenhum nome for informado, será usado `petropolis-map`.
2. O script executa:
   - verificação/instalação de autenticação via `gh auth status`/`gh auth login`;
   - `git init` (se necessário), criação do branch `main`, commit dos arquivos essenciais;
   - criação do repositório remoto com `gh repo create --public --source=. --push` ou apenas `git push` se já existir;
   - configuração automática do GitHub Pages para publicar a partir de `main` e raiz (`/`).
3. Ao final, serão exibidos a URL do repositório e a URL do GitHub Pages (`https://<usuario>.github.io/<repo>/`). Aguarde alguns minutos para o site ficar disponível.

> Se a configuração automática do Pages falhar, configure manualmente em **GitHub → Settings → Pages → Source: Deploy from a branch → Branch: main / Folder: root**.
