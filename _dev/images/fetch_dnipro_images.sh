#!/bin/bash
# LBar Ivano-Frankivsk — загрузка фото с сайта Днепра по SSH.
# Запуск из корня сайта (там, где index.php), рядом должен лежать dnipro-images.tsv:
#   bash fetch_dnipro_images.sh
# Уже скачанные файлы пропускаются, можно запускать повторно.
cd "$(dirname "$0")" || exit 1
LIST="dnipro-images.tsv"
[ -f "$LIST" ] || { echo "Нет файла $LIST рядом со скриптом"; exit 1; }
ok=0; skip=0; fail=0
while IFS=$'\037' read -r dest src fb _rest; do
  [ "$dest" = "dest" ] && continue
  dest="${dest#/}"
  case "$dest" in ""|*..*) continue;; esac
  if [ -s "$dest" ]; then skip=$((skip+1)); continue; fi
  mkdir -p "$(dirname "$dest")"
  if curl -fsSL --max-time 120 -o "$dest" "$src" || { [ -n "$fb" ] && curl -fsSL --max-time 120 -o "$dest" "$fb"; }; then
    ok=$((ok+1)); echo "OK    $dest"
  else
    rm -f "$dest"; fail=$((fail+1)); echo "FAIL  $dest"
  fi
done < <(tr '\t' '\037' < "$LIST")
echo; echo "Скачано: $ok, уже были: $skip, ошибок: $fail"
