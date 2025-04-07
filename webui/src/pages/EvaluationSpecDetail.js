import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Descriptions, Button, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useHistory } from 'react-router-dom';

function EvaluationSpecDetail() {
  const { specId } = useParams();
  const history = useHistory();
  const [spec, setSpec] = useState(null);
  const [loading, setLoading] = useState(false);

  // 获取评估规范详情
  const fetchSpecDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/evaluation-specs/${specId}`);
      if (!response.ok) {
        throw new Error('评估规范未找到');
      }
      const data = await response.json();
      setSpec(data);
    } catch (error) {
      message.error(error.message);
      history.push('/evaluation-specs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpecDetail();
  }, [specId]);

  return (
    <div className="evaluation-spec-detail">
      <Button 
        type="link" 
        icon={<ArrowLeftOutlined />}
        onClick={() => history.goBack()}
        style={{ marginBottom: 16 }}
      >
        返回列表
      </Button>

      <Card 
        title="评估规范详情"
        loading={loading}
      >
        {spec && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="ID">{spec.id}</Descriptions.Item>
            <Descriptions.Item label="名称">{spec.name}</Descriptions.Item>
            <Descriptions.Item label="描述">{spec.description}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{spec.created_at}</Descriptions.Item>
            <Descriptions.Item label="内容">
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(spec.content, null, 2)}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Card>
    </div>
  );
}

export default EvaluationSpecDetail;
