-- ###########################version1.0.0####################
CREATE TABLE IF NOT EXISTS `hziAuth` (
  `_id` int UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '唯一id, 自增',
  `uid` bigint(20) UNSIGNED NOT NULL COMMENT '玩家uid',
  `phone` char(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '手机号',
  PRIMARY KEY (`_id`) USING BTREE COMMENT '主键'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;