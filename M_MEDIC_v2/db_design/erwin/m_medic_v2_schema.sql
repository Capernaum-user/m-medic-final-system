-- MDTS (선박 탑재형 엣지 AI 의료 지원 시스템) Database Schema
-- Tool: ERwin
-- 테이블 순서는 관계를 고려하여 한 번에 실행해도 에러가 발생하지 않게 정렬되었습니다.

-- tb_crew Table Create SQL
-- 테이블 생성 SQL - tb_crew
CREATE TABLE tb_crew
(
    `crew_id`    INT            NOT NULL    AUTO_INCREMENT COMMENT '승조원 고유번호',
    `name`       VARCHAR(50)    NOT NULL    COMMENT '성명',
    `birthdate`  DATE           NOT NULL    COMMENT '생년월일',
    `gender`     CHAR(1)        NOT NULL    COMMENT '성별',
    `bloodtype`  VARCHAR(4)     NOT NULL    COMMENT '혈액형',
    `position`   VARCHAR(50)    NOT NULL    COMMENT '직책',
    `joined_at`  DATETIME       NOT NULL    DEFAULT CURRENT_TIMESTAMP COMMENT '가입 일시',
     PRIMARY KEY (crew_id)
);

-- 테이블 Comment 설정 SQL - tb_crew
ALTER TABLE tb_crew COMMENT '승조원 정보';

-- Index 설정 SQL - tb_crew(name, joined_at)
CREATE INDEX IX_tb_crew_1
    ON tb_crew(name, joined_at);


-- tb_vital Table Create SQL
-- 테이블 생성 SQL - tb_vital
CREATE TABLE tb_vital
(
    `vital_id`     INT             NOT NULL    AUTO_INCREMENT COMMENT '바이탈 고유번호',
    `crew_id`      INT             NOT NULL    COMMENT '승조원 고유번호',
    `heart_rate`   INT             NOT NULL    DEFAULT 0 COMMENT '심박수',
    `spo2`         DECIMAL(5,2)    NOT NULL    DEFAULT 0.0 COMMENT '산소포화도',
    `temperature`  DECIMAL(5,2)    NOT NULL    DEFAULT 0.0 COMMENT '체온',
    `measured_at`  DATETIME        NOT NULL    DEFAULT CURRENT_TIMESTAMP COMMENT '측정 일시',
     PRIMARY KEY (vital_id)
);

-- 테이블 Comment 설정 SQL - tb_vital
ALTER TABLE tb_vital COMMENT '생체 신호 데이터';

-- Index 설정 SQL - tb_vital(measured_at)
CREATE INDEX IX_tb_vital_1
    ON tb_vital(measured_at);

-- Foreign Key 설정 SQL - tb_vital(crew_id) -> tb_crew(crew_id)
ALTER TABLE tb_vital
    ADD CONSTRAINT FK_tb_vital_crew_id_tb_crew_crew_id FOREIGN KEY (crew_id)
        REFERENCES tb_crew (crew_id) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- Foreign Key 삭제 SQL - tb_vital(crew_id)
-- ALTER TABLE tb_vital
-- DROP FOREIGN KEY FK_tb_vital_crew_id_tb_crew_crew_id;


-- tb_analysis Table Create SQL
-- 테이블 생성 SQL - tb_analysis
CREATE TABLE tb_analysis
(
    `analysis_id`      INT                      NOT NULL    AUTO_INCREMENT COMMENT '분석 고유번호',
    `vital_id`         INT                      NOT NULL    COMMENT '바이탈 고유번호',
    `crew_id`          INT                      NOT NULL    COMMENT '승조원 고유번호',
    `analysis_result`  TEXT                     NOT NULL    COMMENT '분석 내용',
    `diagnosis`        VARCHAR(255)             NOT NULL    COMMENT '진단 결과',
    `file_name`        VARCHAR(255)             NOT NULL    COMMENT '파일 이름',
    `file_size`        INT                      NOT NULL    COMMENT '파일 사이즈',
    `file_ext`         VARCHAR(10)              NOT NULL    COMMENT '파일 확장자',
    `risk_level`       ENUM('1','2','3','4')    NOT NULL    COMMENT '위험 등급',
    `analyzed_at`      DATETIME                 NOT NULL    DEFAULT CURRENT_TIMESTAMP COMMENT '분석 일시',
     PRIMARY KEY (analysis_id)
);

-- 테이블 Comment 설정 SQL - tb_analysis
ALTER TABLE tb_analysis COMMENT 'AI 분석';

-- Index 설정 SQL - tb_analysis(analyzed_at)
CREATE INDEX IX_tb_analysis_1
    ON tb_analysis(analyzed_at);

-- Foreign Key 설정 SQL - tb_analysis(vital_id) -> tb_vital(vital_id)
ALTER TABLE tb_analysis
    ADD CONSTRAINT FK_tb_analysis_vital_id_tb_vital_vital_id FOREIGN KEY (vital_id)
        REFERENCES tb_vital (vital_id) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- Foreign Key 삭제 SQL - tb_analysis(vital_id)
-- ALTER TABLE tb_analysis
-- DROP FOREIGN KEY FK_tb_analysis_vital_id_tb_vital_vital_id;


-- tb_logs Table Create SQL
-- 테이블 생성 SQL - tb_logs
CREATE TABLE tb_logs
(
    `log_id`       INT            NOT NULL    AUTO_INCREMENT COMMENT '로그 고유번호',
    `admin_id`     INT            NOT NULL    COMMENT '관리자 고유번호',
    `table_name`   VARCHAR(64)    NOT NULL    COMMENT '대상 테이블명',
    `record_id`    VARCHAR(64)    NOT NULL    COMMENT '대상 레코드',
    `sync_status`  BOOLEAN        NOT NULL    COMMENT '전송 상태',
    `synced_at`    DATETIME       NOT NULL    DEFAULT CURRENT_TIMESTAMP COMMENT '전송 일시',
     PRIMARY KEY (log_id)
);

-- 테이블 Comment 설정 SQL - tb_logs
ALTER TABLE tb_logs COMMENT '육상 서버 동기화 로그';

-- Index 설정 SQL - tb_logs(synced_at)
CREATE INDEX IX_tb_logs_1
    ON tb_logs(synced_at);

-- Foreign Key 설정 SQL - tb_logs(admin_id) -> tb_crew(crew_id)
ALTER TABLE tb_logs
    ADD CONSTRAINT FK_tb_logs_admin_id_tb_crew_crew_id FOREIGN KEY (admin_id)
        REFERENCES tb_crew (crew_id) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- Foreign Key 삭제 SQL - tb_logs(admin_id)
-- ALTER TABLE tb_logs
-- DROP FOREIGN KEY FK_tb_logs_admin_id_tb_crew_crew_id;


-- tb_firstaid Table Create SQL
-- 테이블 생성 SQL - tb_firstaid
CREATE TABLE tb_firstaid
(
    `firstaid_id`   INT         NOT NULL    AUTO_INCREMENT COMMENT '응급처치 고유번호',
    `analysis_id`   INT         NOT NULL    COMMENT '분석 고유번호',
    `crew_id`       INT         NOT NULL    COMMENT '승조원 고유번호',
    `guide_text`    TEXT        NOT NULL    COMMENT '가이드 내용',
    `action_taken`  TEXT        NOT NULL    COMMENT '실제 조치 사항',
    `created_at`    DATETIME    NOT NULL    DEFAULT CURRENT_TIMESTAMP COMMENT '처치 완료 일시',
     PRIMARY KEY (firstaid_id)
);

-- 테이블 Comment 설정 SQL - tb_firstaid
ALTER TABLE tb_firstaid COMMENT '응급 처치';

-- Foreign Key 설정 SQL - tb_firstaid(analysis_id) -> tb_analysis(analysis_id)
ALTER TABLE tb_firstaid
    ADD CONSTRAINT FK_tb_firstaid_analysis_id_tb_analysis_analysis_id FOREIGN KEY (analysis_id)
        REFERENCES tb_analysis (analysis_id) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- Foreign Key 삭제 SQL - tb_firstaid(analysis_id)
-- ALTER TABLE tb_firstaid
-- DROP FOREIGN KEY FK_tb_firstaid_analysis_id_tb_analysis_analysis_id;

-- Foreign Key 설정 SQL - tb_firstaid(crew_id) -> tb_crew(crew_id)
ALTER TABLE tb_firstaid
    ADD CONSTRAINT FK_tb_firstaid_crew_id_tb_crew_crew_id FOREIGN KEY (crew_id)
        REFERENCES tb_crew (crew_id) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- Foreign Key 삭제 SQL - tb_firstaid(crew_id)
-- ALTER TABLE tb_firstaid
-- DROP FOREIGN KEY FK_tb_firstaid_crew_id_tb_crew_crew_id;
