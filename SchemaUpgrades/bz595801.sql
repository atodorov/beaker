use beaker;
CREATE TABLE `beaker_tag` (
    `id` int(11) NOT NULL auto_increment,
    `tag` varchar(20) NOT NULL,i
    `type` varchar(40) NOT NULL,
    PRIMARY KEY  (`id`),
    UNIQUE KEY `tag` (`tag`,`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `retention_tag` (
    `default_` tinyint(1) default '0',
    `id` int(11) NOT NULL default '0',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE recipe_set ADD COLUMN `retention_tag_id` INT NULL AFTER `queue_time`;
ALTER TABLE ADD FOREIGN KEY (`retention_tag_id`) REFERENCES `retention_tag` (`id`);
UPDATE recipe_set SET retention_tag_id = (SELECT id FROM retention_tag where default_ is True) WHERE retention_tag_id is NULL;



