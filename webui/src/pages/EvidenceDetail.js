import React, { useState, useEffect } from 'react';
import { useParams, useHistory } from 'react-router-dom';
import { Button, Descriptions, PageHeader, Spin, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';

function EvidenceDetail() {
  const { id } = useParams();
  const history = useHistory();
  const [loading, setLoading] = useState(true);
  const [evidence, setEvidence] = useState(null);

  // 获取证明材料详情
  const fetchEvidence = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/evidences/${id}`);
      if (!response.ok) {
        throw new Error('获取证明材料详情失败');
      }
      const result = await response.json();
      setEvidence(result);
    } catch (error) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidence();
  }, [id]);

  return (
    <div className="evidence-detail-page">
      <PageHeader
        title="证明材料详情"
        onBack={() => history.goBack()}
        extra={[
          <Button 
            key="edit"
            type="primary"
            onClick={() => history.push(`/evidences/${id}/edit`)}
          >
            编辑
          </Button>
        ]}
      />

      {loading ? (
        <div style={{ textAlign: 'center', padding: '24px' }}>
          <Spin />
        </div>
      ) : (
        <Descriptions bordered column={1}>
          <Descriptions.Item label="ID">{evidence.id}</Descriptions.Item>
          <Descriptions.Item label="名称">{evidence.name}</Descriptions.Item>
          <Descriptions.Item label="描述">{evidence.description}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{evidence.created_at}</Descriptions.Item>
          <Descriptions.Item label="内容">
            <pre style={{ whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(evidence.content, null, 2)}
            </pre>
          </Descriptions.Item>
        </Descriptions>
      )}
    </div>
  );
}

export default EvidenceDetail;
