CREATE TABLE reg(
`id` int not null primary key auto_increment,
`uid` bigint not null,
`nickname` varchar(255) not null,
`date` bigint not null
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE t1(
`id` int not null primary key auto_increment,
`uid` bigint not null,
`nickname` varchar(255) not null,
`win` bigint not null default 0,
`lose` bigint not null default 0
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;