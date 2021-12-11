CREATE TABLE `e1`(
`id` bigint not null primary key auto_increment,
`uid` bigint not null,
`date` bigint not null default 0,
`done` int not null default 0,
`checkin` int not null default 0
);