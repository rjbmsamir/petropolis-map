#!/usr/bin/env bash
set -euo pipefail

BRANCH="main"
REPO_NAME="${1:-petropolis-map}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[ERRO] Dependência não encontrada: $1" >&2
    exit 1
  fi
}

need_cmd git
need_cmd gh

echo "[INFO] Verificando autenticação no GitHub CLI..."
if ! gh auth status >/dev/null 2>&1; then
  echo "[INFO] Executando gh auth login..."
  gh auth login --web --git-protocol https >/dev/null
fi

if [ ! -d .git ]; then
  echo "[INFO] Inicializando repositório git..."
  git init >/dev/null
fi

git symbolic-ref HEAD "refs/heads/${BRANCH}" >/dev/null 2>&1 || git checkout -B "${BRANCH}" >/dev/null

git add index.html README.md publish_github_pages.sh build_map.py camadas >/dev/null 2>&1 || true

if ! git diff --cached --quiet; then
  git commit -m "Publicação inicial" >/dev/null
else
  echo "[INFO] Nenhuma alteração para commitar."
fi

GITHUB_USER=$(gh api user -q .login)
REPO_HTTP="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}"
PAGES_URL="https://${GITHUB_USER}.github.io/${REPO_NAME}/"

if ! gh repo view "${GITHUB_USER}/${REPO_NAME}" >/dev/null 2>&1; then
  echo "[INFO] Criando repositório remoto ${REPO_NAME}..."
  gh repo create "${REPO_NAME}" --public --source=. --push --branch "${BRANCH}" >/dev/null
else
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "${REPO_HTTP}"
  echo "[INFO] Enviando alterações para origin/${BRANCH}..."
  git push origin "${BRANCH}" >/dev/null
fi

PAGES_ENDPOINT="repos/${GITHUB_USER}/${REPO_NAME}/pages"
if gh api "${PAGES_ENDPOINT}" >/dev/null 2>&1; then
  METHOD="PUT"
else
  METHOD="POST"
fi

echo "[INFO] Configurando GitHub Pages (${METHOD})..."
gh api "${PAGES_ENDPOINT}" \
  --method "${METHOD}" \
  -H "Accept: application/vnd.github+json" \
  -f source[branch]="${BRANCH}" \
  -f source[path]="/" >/dev/null || {
    echo "[ALERTA] Não foi possível configurar via API. Configure manualmente: Settings → Pages → Source: Deploy from a branch → main / (root)." >&2
  }

cat <<MSG
[OK] Publicação finalizada.
Repositório: ${REPO_URL}
GitHub Pages: ${PAGES_URL}
Obs.: a propagação do GitHub Pages pode levar alguns minutos.
MSG
