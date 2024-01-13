CREATE TABLE MAMAMI_ITEM (
	mamami_item_id int NOT NULL AUTO_INCREMENT primary key ,
	name varchar(200) NULL,
	model varchar(200) NULL,
	status varchar(50) NULL,
	url varchar(200) NULL,
    item_id varchar(50) NOT NULL
);

CREATE TABLE MAMAMI_ITEM_PART (
	mamami_item_part_id int NOT NULL AUTO_INCREMENT primary key,
	mamami_item_id int NOT NULL,
	option_name varchar(200) NULL,
	stock int NULL,
    foreign key (mamami_item_id) references MAMAMI_ITEM(mamami_item_id) on delete cascade
);