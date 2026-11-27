-- 007 · 2026-11-27 · ИФ: hreflang на страницах курсов (шаблон «Обучение»)
-- База: LBar Ивано-Франковск (impua_lbarfravsk). Выполнить, затем очистить кэш (удалить core/cache/* и «Очистить кэш» в админке).
-- Файл можно выполнять повторно.
SET NAMES utf8mb4;

-- hreflang (uk/ru) на курсах: obucheniye-tatuazh, kurs-pudrovie-brovi: в отдельной шапке не было вызова BabelLinks, как в основном чанке head
UPDATE `Impulse_Digital_X_site_htmlsnippets`
   SET `snippet`=REPLACE(`snippet`, '<link rel="icon" href="favicon.ico" type="image/x-icon">', '<link rel="icon" href="favicon.ico" type="image/x-icon">\n    [[BabelLinks?\n        &showCurrent=`1`\n        &tpl=`babelLinkHeadAlternate`\n    ]]')
 WHERE `name` IN ('head-study') AND `snippet` NOT LIKE '%BabelLinks%';
