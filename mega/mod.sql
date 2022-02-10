CREATE TABLE bw(
    `id` INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `uid` BIGINT NOT NULL,
    `nickname` VARCHAR(255) NOT NULL,
    `total` INT NOT NULL DEFAULT 0,
    `win` INT NOT NULL DEFAULT 0,
    `mvp` INT NOT NULL DEFAULT 0,
    `date` BIGINT DEFAULT 0
);