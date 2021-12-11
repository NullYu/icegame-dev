CREATE TABLE IF NOT EXISTS `reship` (
    `id` bigint not null primary key,
    `uid` bigint not null,
    `date` bigint not null default 0,
    `pending` int not null default 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;