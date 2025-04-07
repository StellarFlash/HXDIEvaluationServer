import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div className="home">
      <h1>评估系统管理平台</h1>
      <div className="dashboard">
        <Link to="/evaluation-specs" className="card">
          <h2>评估规范管理</h2>
          <p>上传、查看和管理评估规范</p>
        </Link>
        <Link to="/evidences" className="card">
          <h2>证明材料管理</h2>
          <p>上传、查看和管理证明材料</p>
        </Link>
        <Link to="/reports" className="card">
          <h2>报告管理</h2>
          <p>生成、查看和管理评估报告</p>
        </Link>
        <Link to="/database" className="card">
          <h2>数据库管理</h2>
          <p>初始化和管理数据库</p>
        </Link>
      </div>
    </div>
  );
}

export default Home;
