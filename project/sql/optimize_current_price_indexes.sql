-- 为 current_price 表添加索引以优化全国界面图表查询性能
-- 执行前请确认表名和字段名与实际数据库一致

-- 1. 城市名称索引（用于城市搜索、筛选）
CREATE INDEX idx_city_name ON current_price(city_name);

-- 2. 省份名称索引（用于省份筛选）
CREATE INDEX idx_province_name ON current_price(province_name);

-- 3. 区县名称索引（用于区县查询）
CREATE INDEX idx_district_name ON current_price(district_name);

-- 4. 城市均价索引（用于价格排序、分级）
CREATE INDEX idx_city_avg_price ON current_price(city_avg_price);

-- 5. 挂牌量索引（用于挂牌量排行）
CREATE INDEX idx_listing_count ON current_price(listing_count);

-- 6. 区县涨跌比索引（用于涨跌榜排序）
CREATE INDEX idx_district_ratio ON current_price(district_ratio);

-- 7. 组合索引：城市+区县（用于同城区县对比）
CREATE INDEX idx_city_district ON current_price(city_name, district_name);

-- 8. 组合索引：省份+城市（用于省份下的城市查询）
CREATE INDEX idx_province_city ON current_price(province_name, city_name);

-- 9. 组合索引：城市均价+挂牌量（用于城市分级气泡图）
CREATE INDEX idx_price_listing ON current_price(city_avg_price, listing_count);

-- 查看索引创建结果
SHOW INDEX FROM current_price;
