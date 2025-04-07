import React, { useState, useEffect } from 'react';
import { Table, Button, PageHeader, Spin, message } from 'antd';
import { useHistory } from 'react-router-dom';
import { PlusOutlined } from '@ant-design/icons';

function Reports() {
  const history = useHistory();
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          onClick={() => history.push(`/reports/${record.id}`)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  const fetchReports = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const start = (page - 1) * pageSize;
      const end = start + pageSize - 1;
      const response = await fetch(`/api/reports?start=${start}&end=${end}`);
      if (!response.ok) {
        throw new Error('获取报告列表失败');
      }
      const result = await response.json();
      setReports(result.reports);
      setPagination({
        ...pagination,
        current: page,
        total: result.total
      });
    } catch (error) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  return (
    <div className="reports-page">
      <PageHeader
        title="报告列表"
        extra={[
          <Button
            key="create"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => history.push('/reports/new')}
          >
            新建报告
          </Button>
        ]}
      />

      <Table
        columns={columns}
        dataSource={reports}
        loading={loading}
        pagination={pagination}
        onChange={(pagination) => fetchReports(pagination.current, pagination.pageSize)}
        rowKey="id"
      />
    </div>
  );
}

export default Reports;
