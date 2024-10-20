CREATE TABLE EMP (
    EMPNO int PRIMARY KEY,
    ENAME varchar NOT NULL,
    JOB varchar NOT NULL,
    MGR int,
    HIREDATE date NOT NULL,
    SAL int NOT NULL,
    COMM int NOT NULL,
    DEPTNO int NOT NULL,
    SLACKER boolean NOT NULL
);

CREATE TABLE DEPT (
    DEPTNO int PRIMARY KEY,
    NAME varchar  NOT NULL
);

CREATE TABLE BONUS (
    ENAME varchar  NOT NULL,
    JOB varchar  NOT NULL,
    SAL int  NOT NULL,
    COMM int  NOT NULL
);

CREATE TABLE EMPNULLABLES (
    EMPNO int PRIMARY KEY,
    ENAME varchar,
    JOB varchar,
    MGR int,
    HIREDATE date,
    SAL int,
    COMM int,
    DEPTNO int,
    SLACKER boolean
);

CREATE TABLE EMPNULLABLES_20 (
    EMPNO int PRIMARY KEY,
    ENAME varchar,
    JOB varchar,
    MGR int,
    HIREDATE date,
    SAL int,
    COMM int,
    DEPTNO int,
    SLACKER boolean
);

CREATE TABLE EMP_B (
    EMPNO int PRIMARY KEY,
    ENAME varchar  NOT NULL,
    JOB varchar  NOT NULL,
    MGR int,
    HIREDATE date  NOT NULL,
    SAL int  NOT NULL,
    COMM int  NOT NULL,
    DEPTNO int  NOT NULL,
    SLACKER boolean  NOT NULL,
    BIRTHDATE date  NOT NULL
);
