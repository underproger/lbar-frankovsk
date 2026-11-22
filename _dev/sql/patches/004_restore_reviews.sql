-- 004 · 2026-11-22 · вернуть отзывы, перенесённые с сайта Днепра (как были опубликованы на Днепре)
-- 140 отзывов, рейтинги 22 веток, 126 скриншотов отзывов на странице «Отзывы».
-- Ссылка «Читать все отзывы» на Google-карты студии в Днепре остаётся выключенной.
UPDATE `Impulse_Digital_X_ec_messages` SET `published`=1 WHERE `id` IN (122,123,124,125,126,127,151,152,153,154,155,156,177,178,179,199,200,201,202,241,242,243,245,246,247,248,250,251,252,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,331,332,345,346,347,348,349,350,351,352,353,354,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,406,407,408,409,410,411,412,413,415,416,417,427,428,429,470,471,472,473,474,475,476,477,519,520,521,522,523,524,538,541,543,544,554,555,556,557,558,559,560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,580,581,582,583,584,585,586,587);
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=7;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=6 WHERE `id`=11;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=51;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=3 WHERE `id`=87;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=88;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=89;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=3 WHERE `id`=90;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=5 WHERE `id`=93;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=100;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=15 WHERE `id`=101;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=116;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=6 WHERE `id`=117;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=118;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=3 WHERE `id`=119;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=5 WHERE `id`=120;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=122;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=15 WHERE `id`=124;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=3 WHERE `id`=127;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=131;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=4 WHERE `id`=137;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=3 WHERE `id`=187;
UPDATE `Impulse_Digital_X_ec_threads` SET `rating_simple`='5.000000', `rating_wilson`='5.000000', `count`=3 WHERE `id`=188;
UPDATE `Impulse_Digital_X_ms2_resource_files` SET `active`=1 WHERE `id` IN (6211,6212,6213,6214,6215,6216,6217,6218,6219,6220,6221,6222,6223,6224,6225,6226,6227,6228,6229,6230,6231,6232,6233,6234,6235,6236,6237,6238,6239,6240,6241,6242,6243,6244,6245,6246,6247,6248,6249,6250,6251,6252,6253,6254,6255,6256,6257,6258,6259,6260,6261,6262,6263,6264,6265,6266,6267,6268,6269,6270,6271,6272,6273,7180,7181,7182,7183,7184,7185,7186,7187,7188,7189,7190,7191,7192,7193,7194,7195,7196,7197,7198,7199,7200,7201,7202,7203,7204,7205,7206,7207,7208,7209,7210,7211,7212,7213,7214,7215,7216,7217,7218,7219,7220,7221,7222,7223,7224,7225,7226,7227,7228,7229,7230,7231,7232,7233,7234,7235,7236,7237,7238,7239,7240,7241,7242);
-- После применения: очистить core/cache/.
