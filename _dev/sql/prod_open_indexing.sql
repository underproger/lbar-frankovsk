-- LBar Ivano-Frankivsk: открыть сайт для индексации (выполнять на бою, когда сайт готов к запуску)
-- Сейчас в чанке head жёстко стоит noindex nofollow (как на тесте и на сайте Днепра).
-- После запроса robots берётся из TV «robot» страницы, по умолчанию index, follow.
-- Страница «Спасибо» остаётся закрытой (patches/002). После выполнения — очистить кэш.
SET NAMES utf8mb4;
UPDATE `Impulse_Digital_X_site_htmlsnippets`
   SET `snippet`=REPLACE(`snippet`, '<meta name="robots" content="noindex nofollow" />', '<meta name="robots" content="{$_modx->resource.robot ?: ''index, follow''}" />')
 WHERE `name`='head';

-- Обратно закрыть, если понадобится:
-- UPDATE `Impulse_Digital_X_site_htmlsnippets` SET `snippet`=REPLACE(`snippet`, '<meta name="robots" content="{$_modx->resource.robot ?: ''index, follow''}" />', '<meta name="robots" content="noindex nofollow" />') WHERE `name`='head';
