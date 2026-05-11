-- 1. 기존 데이터베이스 확인 (이미 생성되어 있음)
USE MDTS;

-- 2. 전용 사용자 'mdts' 생성 (외부 접속 가능하도록 '%' 설정)
CREATE USER IF NOT EXISTS 'mdts'@'%' IDENTIFIED BY '12345';

-- 3. MDTS 데이터베이스에 대한 모든 권한 부여
GRANT ALL PRIVILEGES ON MDTS.* TO 'mdts'@'%';

-- 4. 변경 사항 적용
FLUSH PRIVILEGES;

-- 5. 권한 확인 (선택 사항)
SHOW GRANTS FOR 'mdts'@'%';
