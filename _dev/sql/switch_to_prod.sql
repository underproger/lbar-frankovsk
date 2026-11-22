-- LBar Ivano-Frankivsk: перевод базы с тестового адреса на боевой https://lbar.com.ua/ivano-frankivsk/
-- Выполнить ПОСЛЕ импорта lbar_ivano_frankivsk_test.sql в боевую базу. Потом очистить core/cache/.

UPDATE `Impulse_Digital_X_context_setting` SET `value`='/ivano-frankivsk/'                        WHERE `context_key`='ua'  AND `key`='base_url';
UPDATE `Impulse_Digital_X_context_setting` SET `value`='https://lbar.com.ua/ivano-frankivsk/'     WHERE `context_key`='ua'  AND `key`='site_url';
UPDATE `Impulse_Digital_X_context_setting` SET `value`='/ivano-frankivsk/ru/'                     WHERE `context_key`='web' AND `key`='base_url';
UPDATE `Impulse_Digital_X_context_setting` SET `value`='https://lbar.com.ua/ivano-frankivsk/ru/'  WHERE `context_key`='web' AND `key`='site_url';

-- cookie сессии на всю папку сайта (иначе на UA-страницах не работают формы), см. patches/001
INSERT INTO `Impulse_Digital_X_context_setting` (`context_key`,`key`,`value`,`xtype`,`namespace`,`area`,`editedon`) VALUES
 ('web','session_cookie_path','/ivano-frankivsk/','textfield','core','session',NOW()),
 ('ua','session_cookie_path','/ivano-frankivsk/','textfield','core','session',NOW())
ON DUPLICATE KEY UPDATE `value`=VALUES(`value`);

-- Индексация. На тесте в чанке head жёстко стоит noindex (так же, как сейчас на сайте Днепра).
-- Когда сайт будет готов к открытию — раскомментируйте строку ниже: robots возьмётся из TV «robot» страницы (по умолчанию index, follow).
-- UPDATE `Impulse_Digital_X_site_htmlsnippets` SET `snippet`=REPLACE(`snippet`, '<meta name="robots" content="noindex nofollow" />', '<meta name="robots" content="{$_modx->resource.robot ?: ''index, follow''}" />') WHERE `name`='head';
