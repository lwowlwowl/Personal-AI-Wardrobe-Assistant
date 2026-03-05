-- 将 is_favorite 从 Boolean 改为 Integer (0-3)，与前端收藏等级一致
-- 执行前请备份数据库。在 psql 或 pgAdmin 中连接 wardrobe_db 后执行。
--
-- 已有数据：false -> 0, true -> 1

ALTER TABLE clothing_items
  ALTER COLUMN is_favorite TYPE INTEGER
  USING (CASE WHEN is_favorite = true THEN 1 ELSE 0 END);

-- 设置默认值
ALTER TABLE clothing_items
  ALTER COLUMN is_favorite SET DEFAULT 0;
