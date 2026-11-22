-- 001 · 2026-11-22 · cookie сессии на весь сайт
-- Проблема: index.php поднимает контекст web (RU, base_url /ru/), поэтому PHPSESSID ставился с path=/ru/
-- и на украинских страницах сессия не сохранялась (AjaxForm хранит настройки формы в сессии -> формы в UA не отправляются).
-- Тест (корень домена):
INSERT INTO `Impulse_Digital_X_context_setting` (`context_key`,`key`,`value`,`xtype`,`namespace`,`area`,`editedon`) VALUES
 ('web','session_cookie_path','/','textfield','core','session',NOW()),
 ('ua','session_cookie_path','/','textfield','core','session',NOW())
ON DUPLICATE KEY UPDATE `value`=VALUES(`value`);
-- На бою вместо '/' будет '/ivano-frankivsk/' (уже добавлено в switch_to_prod.sql).
-- После применения: очистить core/cache/.
