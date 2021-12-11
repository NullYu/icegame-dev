CREATE TABLE bw(
    `id` INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `winnerTeam` VARCHAR(255) NOT NULL,
    `winRec` VARCHAR(255) NOT NULL,
    -- win record format:
    -- uid1/uid2/uid3/uid4
    -- decode with: <object>.split('/')
    `date` BIGINT DEFAULT 0
);
