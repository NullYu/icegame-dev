CREATE TABLE `expdData`(
    `id` INT NOT NULL PRIMARY KEY auto_increment,
    `uid` BIGINT NOT NULL,
    `startDate` BIGINT NOT NULL DEFAULT 0,
    `endDate` BIGINT NOT NULL DEFAULT -1,
    `reason` VARCHAR(255) NOT NULL,
    `valid` INT NOT NULL DEFAULT 1
);
ALTER TABLE expdData ADD INDEX k_uid(uid);