-- 修复 clothing_items.season 列类型不匹配
-- 原因：表中 season 为单枚举 clothingseason，而代码传入数组 clothingseason[]
-- 执行前请备份数据库。在 psql 或 pgAdmin 中连接 wardrobe_db 后执行。
--
-- 若报错 "type clothingseason[] does not exist"，请先查看枚举类型名：
--   \dT+   -- 列出所有类型，确认枚举名（可能带 schema，如 public.clothingseason）
-- 若枚举名为其它（如 clothingseason_enum），把下面两处 clothingseason 替换成实际类型名。

-- 将 season 从单枚举改为枚举数组（已有数据：单值转为单元素数组）
ALTER TABLE clothing_items
  ALTER COLUMN season TYPE clothingseason[]
  USING (
    CASE
      WHEN season IS NULL THEN NULL
      ELSE ARRAY[season]::clothingseason[]
    END
  );

-- 与 models.py 中 Index('idx_clothing_season', 'season', postgresql_using="gin") 一致，用于数组查询加速；若表是早期建的可能没有此索引
CREATE INDEX IF NOT EXISTS idx_clothing_season
  ON clothing_items
  USING gin (season);
