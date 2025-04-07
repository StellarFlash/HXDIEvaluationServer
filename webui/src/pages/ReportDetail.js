import React, { useState, useEffect } from 'react';
import { useParams, useHistory } from 'react-router-dom';
import { PageHeader, Descriptions, Card, Spin, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';

function ReportDetail() {
  const { reportId } = useParams();
  const history = useHistory();
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState(null);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/reports/${reportId}`);
      if (!response.ok) {
        throw new Error('获取报告详情失败');
      }
      const result = await response.json();
      setReport({
        ...result,
        evaluation_spec: result.evaluation_spec ? JSON.parse(result.evaluation_spec) : null,
        evidences: result.evidences ? result.evidences.map(e => JSON.parse(e)) : []
      });
    } catch (error) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [reportId]);

  if (loading) {
    return <Spin size="large" />;
  }

  return (
    <div className="report-detail-page">
      <PageHeader
        title="报告详情"
        onBack={() => history.goBack()}
        extra={[
          <Button
            key="back"
            icon={<ArrowLeftOutlined />}
            onClick={() => history.goBack()}
          >
            返回
          </Button>
        ]}
      />

      <Descriptions title="基本信息" bordered>
        <Descriptions.Item label="ID">{report.id}</Descriptions.Item>
        <Descriptions.Item label="名称">{report.name}</Descriptions.Item>
        <Descriptions.Item label="创建时间">{report.created_at}</Descriptions.Item>
      </Descriptions>

      <Card title="评估规范" style={{ marginTop: 16 }}>
        {report.evaluation_spec ? (
          <pre>{JSON.stringify(report.evaluation_spec, null, 2)}</pre>
        ) : (
          <span>无评估规范</span>
        )}
      </Card>

      <Card title="证明材料" style={{ marginTop: 16 }}>
        {report.evidences.length > 0 ? (
          report.evidences.map((evidence, index) => (
            <Card key={index} style={{ marginBottom: 16 }}>
              <pre>{JSON.stringify(evidence, null, 2)}</pre>
            </Card>
          ))
        ) : (
          <span>无证明材料</span>
        )}
      </Card>
    </div>
  );
}

export default ReportDetail;
