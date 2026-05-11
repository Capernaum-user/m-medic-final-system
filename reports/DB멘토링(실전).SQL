[DB멘토링:실전] 김광진 --> router128@hanmail.net

팀명: MDTS
팀원: 송승현/최재선/권태향/이엘리사/김태용/김명기 
주제: 선박 탑재형 엣지 AI 의료 지원 시스템-Meditising MDTS

* 데이터 모델링 주소: 

URL : https://aquerytool.com/aquerymain/index/?rurl=b6a079c0-f70b-4aff-8d02-1ff8ee9512be&
Password : y1s485






// 승조원 정보 
public class CrewDTO {

    // 승조원 고유번호 
    private Integer crew_id;

    // 성명 
    private String name;

    // 생년월일 
    private Date birthdate;

    // 성별 
    private String gender;

    // 혈액형 
    private String bloodtype;

    // 직책 
    private String position;

    // 가입 일시 
    private Timestamp joined_at;

    public Integer getCrewId() {
        return crew_id;
    }

    public void setCrewId(Integer crewId) {
        this.crew_id = crew_id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Date getBirthdate() {
        return birthdate;
    }

    public void setBirthdate(Date birthdate) {
        this.birthdate = birthdate;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public String getBloodtype() {
        return bloodtype;
    }

    public void setBloodtype(String bloodtype) {
        this.bloodtype = bloodtype;
    }

    public String getPosition() {
        return position;
    }

    public void setPosition(String position) {
        this.position = position;
    }

    public Timestamp getJoinedAt() {
        return joined_at;
    }

    public void setJoinedAt(Timestamp joinedAt) {
        this.joined_at = joined_at;
    }

    // tb_crew 모델 복사
    public void CopyData(tb_crew param)
    {
        this.crew_id = param.getCrewId();
        this.name = param.getName();
        this.birthdate = param.getBirthdate();
        this.gender = param.getGender();
        this.bloodtype = param.getBloodtype();
        this.position = param.getPosition();
        this.joined_at = param.getJoinedAt();
    }
}

* 산소포화도(SPO2), 체중, 키 등등 실수 데이터의 처리 

  산소포화도: 95.5%
  체중: 35.0 kg
       78.3 kg
      127.5 kg      <=======  DECIMAL(5,2)=NUMERIC(5,2)
  키: 130.2 cm
      178.8 cm
      230.1 cm 
   
* 이미지 파일 처리하기 

  file_folder = 'd:/uploads/';
  file_name = 'image0001.jpg';
  file_path = file_folder + file_name; <== 폭망!
  (1)'d:/uploads/image0001.jpg';
  
  file_basename = 'image0001';
  file_size = 230420;
  file_ext = '.jpg';

  file_basename + '_' + xxxxxxx + file_ext;
  : 'image0001_2f48f241-9d64-4d16-bf56-70b9d4e0e79a.jpg';

  xxxxxx : UUID(Unversally Unique IDentifier, 우주에서 유일한 식별자)

  * 
  import java.util.UUID;

public class Main {

    public static void main(String[] args) {
        String uuid = UUID.randomUUID().toString();

        System.out.println(uuid);
    }
}
# 2f48f241-9d64-4d16-bf56-70b9d4e0e79a 


select uuid(); -- 초당 100만회 * 86년간 중복성 회피됨.
# d93afefb-386f-11f1-85ad-d45d641d8d70
# e13cedd4-386f-11f1-85ad-d45d641d8d70
# e4ba1d67-386f-11f1-85ad-d45d641d8d70

* INT 데이터 

  INT ... 32 bit 정수(-2147483648~+2147483647) * -21억~+21억
---------------------------------------------------------------------
(실전프로젝트 MySQL SQL문)
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
    `firstaid_id`   INT         NOT NULL    AUTO_INCREMENT COMMENT '응급처지 고유번호', 
    `analysis_id`   INT         NOT NULL    COMMENT '분석 고유번호', 
    `crew_id`       INT         NOT NULL    COMMENT '승조원 고유번호', 
    `guide_text`    TEXT        NOT NULL    COMMENT '가이즈 내용', 
    `action_taken`  TEXT        NOT NULL    COMMENT '실제 조치 사항', 
    `created_at`    DATETIME    NOT NULL    DEFAULT CURRENT_TIMESTAMP COMMENT '처치 완료 일시', 
     PRIMARY KEY (firstaid_id)
);

-- 테이블 Comment 설정 SQL - tb_firstaid
ALTER TABLE tb_firstaid COMMENT '응급 처지';

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