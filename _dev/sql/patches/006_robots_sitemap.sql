-- 006 · 2026-11-27 · robots.txt сайта ИФ и sitemap без страницы «Спасибо»
-- Выполнять на бою после switch_to_prod.sql (можно и на тесте — там всё равно закрыто заголовком X-Robots-Tag).
-- После — очистить кэш.
SET NAMES utf8mb4;

-- 1. https://lbar.com.ua/ivano-frankivsk/robots.txt (ресурс 197, был снят с публикации).
--    Поисковики его не читают — действует только корневой lbar.com.ua/robots.txt, —
--    но содержимое совпадает с правилами ИФ в корневом файле.
UPDATE `Impulse_Digital_X_site_content`
   SET `content`='# Пошуковики читають лише https://lbar.com.ua/robots.txt у корені домену.\n# Тут — ті самі правила для сайту Івано-Франківська, щоб файл у папці не суперечив кореневому.\nUser-agent: *\nDisallow: /ivano-frankivsk/impulsemanager/\nDisallow: /ivano-frankivsk/assets/components/\nDisallow: /ivano-frankivsk/core/\nDisallow: /ivano-frankivsk/connectors/\nDisallow: /ivano-frankivsk/index.php\nDisallow: *?\nAllow: /ivano-frankivsk/assets/components/*.css\nAllow: /ivano-frankivsk/assets/components/*.js\nAllow: /*.js\nAllow: /*.css\nAllow: /*.jpg\nAllow: /*.gif\nAllow: /*.png\n\nSitemap: https://lbar.com.ua/ivano-frankivsk/sitemap.xml\nSitemap: https://lbar.com.ua/ivano-frankivsk/ru/sitemap.xml', `published`=1, `publishedon`=UNIX_TIMESTAMP(), `searchable`=0, `editedon`=UNIX_TIMESTAMP()
 WHERE `id`=197 AND `alias`='robots';

-- 2. Страница «Спасибо» (UA 269, RU 40) закрыта noindex, а в sitemap.xml попадала.
--    Ставим ей галочку TV «exclude» (по ней pdoSitemap и отсекает страницы) и показываем этот TV в шаблоне «Success-Page-RU».
INSERT IGNORE INTO `Impulse_Digital_X_site_tmplvar_templates` (`tmplvarid`,`templateid`,`rank`) VALUES (7,6,0);
DELETE FROM `Impulse_Digital_X_site_tmplvar_contentvalues` WHERE `tmplvarid`=7 AND `contentid` IN (40,269);
INSERT INTO `Impulse_Digital_X_site_tmplvar_contentvalues` (`tmplvarid`,`contentid`,`value`) VALUES (7,40,'1'),(7,269,'1');
