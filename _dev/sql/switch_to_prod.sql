-- LBar Ivano-Frankivsk: перенос базы с теста на боевой адрес https://lbar.com.ua/ivano-frankivsk/
-- Порядок: 1) импортировать в боевую базу дамп с теста; 2) выполнить этот файл;
--          3) удалить всё в core/cache/; 4) зайти в админку и нажать «Очистить кэш».
-- Файл можно выполнять повторно: все запросы просто перезаписывают значения.
-- Проверено на дампе теста от 2026-11-27.
SET NAMES utf8mb4;

-- 1. Адреса контекстов: українська (ua) — у корені папки, російська (web) — у /ru/
UPDATE `Impulse_Digital_X_context_setting` SET `value`='/ivano-frankivsk/'                       WHERE `context_key`='ua'  AND `key`='base_url';
UPDATE `Impulse_Digital_X_context_setting` SET `value`='https://lbar.com.ua/ivano-frankivsk/'    WHERE `context_key`='ua'  AND `key`='site_url';
UPDATE `Impulse_Digital_X_context_setting` SET `value`='/ivano-frankivsk/ru/'                    WHERE `context_key`='web' AND `key`='base_url';
UPDATE `Impulse_Digital_X_context_setting` SET `value`='https://lbar.com.ua/ivano-frankivsk/ru/' WHERE `context_key`='web' AND `key`='site_url';

-- 2. Cookie сессии — на всю папку сайта, но не на весь lbar.com.ua (не пересекается с /dnipro/ и корнем)
INSERT INTO `Impulse_Digital_X_context_setting` (`context_key`,`key`,`value`,`xtype`,`namespace`,`area`,`editedon`) VALUES
 ('web','session_cookie_path','/ivano-frankivsk/','textfield','core','session',NOW()),
 ('ua','session_cookie_path','/ivano-frankivsk/','textfield','core','session',NOW())
ON DUPLICATE KEY UPDATE `value`=VALUES(`value`);
-- своё имя cookie сессии вместо общего PHPSESSID, чтобы не пересекаться с другими сайтами на lbar.com.ua
-- (cookie админки тоже ограничен папкой /ivano-frankivsk/ — это MODX делает сам по base_url из конфига)
UPDATE `Impulse_Digital_X_system_settings` SET `value`='lbarif_sess' WHERE `key`='session_name';

-- 3. Ссылки от корня домена, которые в подпапке уходили бы на https://lbar.com.ua/...
-- 3.1 Страница «Спасибо» (UA и RU): кнопка «Повернутися на головну» вела на корень домена
UPDATE `Impulse_Digital_X_site_templates`
   SET `content`=REPLACE(`content`, '<a href="/" class="btn-send">', '<a href="[[++site_url]]" class="btn-send">')
 WHERE `id`=6;
-- 3.2 Галочки в баннере на страницах услуг (шаблон «Категория», 18 страниц)
UPDATE `Impulse_Digital_X_site_snippets`
   SET `snippet`=REPLACE(`snippet`, 'src="/images/design/merit.svg"', 'src="images/design/merit.svg"')
 WHERE `name`='bannerBenefits';
-- 3.3 Фото в блоках «Оборудование» и «Специалисты» (шаблон «Категория NEW», сейчас не используется — на будущее)
UPDATE `Impulse_Digital_X_site_snippets`
   SET `snippet`=REPLACE(`snippet`, 'src="/<?=$item[', 'src="<?=$item[')
 WHERE `name` IN ('getEquipmentList','getSpecialiststList');
-- 3.4 Конвертер WebP в админке: скрипт кнопки грузился с /connectors/ в корне домена.
--     Вместе с этим заменить файл connectors/converter/converter.js
UPDATE `Impulse_Digital_X_site_plugins`
   SET `plugincode`=REPLACE(`plugincode`, 'addJavascript(''/connectors/converter/converter.js'')', 'addJavascript(MODX_CONNECTORS_URL.''converter/converter.js'')')
 WHERE `name`='modx_plugin_webp_converter';

-- 4. Старые сессии тестового домена больше не нужны (после переноса все просто войдут заново)
TRUNCATE TABLE `Impulse_Digital_X_session`;
