CREATE TABLE IF NOT EXISTS `reports` (
  `id` int unsigned primary key auto_increment COMMENT 'data id',
  `reporterUid` bigint not null COMMENT 'player uid',
  `targetUid` bigint default 0 COMMENT 'target uid',
  `reportTime` bigint not null COMMENT 'report time',
  `reason` varchar(255) NOT NULL COMMENT 'reason',
  INDEX `idx_serverType` (serverType)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
