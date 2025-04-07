import React, { useState, useEffect } from 'react';
import { Table, Button, Input, Space, message } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useHistory } from 'react-router-dom';

const PAGE_SIZE = 10;

function Evidences() {
  const history = useHistory();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: PAGE_SIZE,
    total: 0
  });
  const [searchText, setSearchText] = useState('');

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
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 200,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Button 
          type="link"
          onClick={() => history.push(`/evidences/${record.id}`)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  // 获取证明材料列表
  const fetchEvidences = async (page = 1, pageSize = PAGE_SIZE) => {
    setLoading(true);
    try {
      const start = (page - 1) * pageSize;
      const end = start + pageSize - 1;
      const response = await fetch(`/api/evidences?start=${start}&end=${end}`);
      if (!response.ok) {
        throw new Error('获取证明材料列表失败');
      }
      const result = await response.json();
      setData(result.evidences);
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

  // 处理分页变化
  const handleTableChange = (pagination) => {
    fetchEvidences(pagination.current, pagination.pageSize);
  };

  // 处理搜索
  const handleSearch = () => {
    // TODO: 实现搜索功能
    message.info('搜索功能待实现');
  };

  useEffect(() => {
    fetchEvidences();
  }, []);

  return (
    <div className="evidences-page">
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Input
            placeholder="搜索证明材料"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
          <Button 
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleSearch}
          >
            搜索
          </Button>
          <Button 
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => history.push('/evidences/new')}
          >
            新建
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        rowKey="id"
      />
    </div>
  );
}

export default Evidences;
