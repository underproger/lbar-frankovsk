-- 002 · 2026-11-22 · страница «Спасибо за заявку» (thanx-you, RU id 40 / UA id 269) закрыта от индексации
-- В шаблоне Success-Page-RU не было meta robots вообще. Действует и на тесте, и на бою.
UPDATE `Impulse_Digital_X_site_templates`
SET `content` = REPLACE(`content`, '<meta http-equiv="X-UA-Compatible" content="IE=edge" />',
                                   '<meta http-equiv="X-UA-Compatible" content="IE=edge" />\n    <meta name="robots" content="noindex, nofollow" />')
WHERE `id` = 6 AND `content` NOT LIKE '%name="robots"%';
-- После применения: очистить core/cache/.
