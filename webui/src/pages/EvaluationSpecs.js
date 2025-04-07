import React, { useState, useEffect } from 'react';
import { Table, Button, Space, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';

function EvaluationSpecs() {
  const [specs, setSpecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 获取评估规范列表
  const fetchSpecs = async (start = 0, end = 9) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/evaluation-specs?start=${start}&end=${end}`);
      const data = await response.json();
      setSpecs(data.evaluation_specs);
      setPagination(prev => ({
        ...prev,
        total: data.total
      }));
    } catch (error) {
      message.error('获取评估规范列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理分页变化
  const handleTableChange = (pagination) => {
    const { current, pageSize } = pagination;
    const start = (current - 1) * pageSize;
    const end = start + pageSize - 1;
    fetchSpecs(start, end);
    setPagination(pagination);
  };

  useEffect(() => {
    fetchSpecs();
  }, []);

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Link to={`/evaluation-specs/${record.id}`}>{text}</Link>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 200
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Link to={`/evaluation-specs/${record.id}`}>查看</Link>
        </Space>
      )
    }
  ];

  return (
    <div className="evaluation-specs">
      <div style={{ marginBottom: 16 }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => message.info('上传新评估规范')}
        >
          上传新规范
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={specs}
        rowKey="id"
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        scroll={{ x: 800 }}
      />
    </div>
  );
}

export default EvaluationSpecs;
