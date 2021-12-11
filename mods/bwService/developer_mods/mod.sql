
mysql> create table unranked(
    -> `id` int primary key not null auto_increment,
    -> `mode` varchar(255) not null default 'generic',
    -> `p1` bigint not null,
    -> `p2` bigint not null,
    -> `winner` bigint not null,
    -> `date` bigint not null default 0,
    -> `duration` bigint not null default 0,
    -> `byDisconnection` int not null default 0
    -> );
