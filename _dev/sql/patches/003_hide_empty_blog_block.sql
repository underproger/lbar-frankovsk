-- 003 · 2026-11-22 · пустой блок «Статьи» с кнопкой «Детальніше» на главной и всех услугах
-- Блок bl-blog выводит 3 статьи из TV title-st-* / link-st-* / img-st-*; на сайте они не заполнены
-- (блог не опубликован), поэтому выводилась пустая карточка с одной кнопкой «Детальніше».
-- Теперь блок показывается, только если заполнена первая статья (TV title-st-1).
UPDATE `Impulse_Digital_X_site_templates`
SET `content` = REPLACE(`content`, '[[$bl-blog]]', '[[*title-st-1:notempty=`[[$bl-blog]]`]]')
WHERE `id` IN (1, 8) AND `content` NOT LIKE '%title-st-1:notempty%';
-- После применения: очистить core/cache/.
