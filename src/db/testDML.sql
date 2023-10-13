-- <mamami_item... test>
-- insert into mamami_item(mamami_item_id, name, model, status, url, item_id) values(1,'제품','모델','판매중','http',123);

-- insert into mamami_item_part(mamami_item_id,option_name,stock) values(1,'블랙',3);
-- insert into mamami_item_part(mamami_item_id,option_name,stock) values(1,'갈색',3);
-- insert into mamami_item_part(mamami_item_id,option_name,stock) values(1,'3mm',-1);

select distinct * from mamami_item a join mamami_item_part b on a.mamami_item_id=b.mamami_item_id order by b.mamami_item_part_id asc LIMIT 10000;
-- select count(*) from mamami_item;
-- select count(*) from mamami_item_part;

-- <ENABLE SAFE MODE(safe mode 비활성화)>
-- SET SQL_SAFE_UPDATES = 0;
-- delete from mamami_item;
-- select * from mamami_item;
-- <ENABLE SAFE MODE(safe mode 활성화)>
-- SET SQL_SAFE_UPDATES = 1;