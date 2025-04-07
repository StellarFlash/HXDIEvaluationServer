import React, { useState } from 'react';
import { Upload, Button, message, PageHeader } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useHistory } from 'react-router-dom';

const { Dragger } = Upload;

function UploadPage() {
  const history = useHistory();
  const [uploading, setUploading] = useState(false);

  const props = {
    name: 'files',
    multiple: true,
    action: '/api/evidences/upload',
    accept: '.docx',
    beforeUpload: (file) => {
      const isDocx = file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      if (!isDocx) {
        message.error('仅支持上传.docx文件');
      }
      return isDocx;
    },
    onChange(info) {
      const { status } = info.file;
      if (status === 'uploading') {
        setUploading(true);
      }
      if (status === 'done') {
        setUploading(false);
        message.success(`${info.file.name} 文件上传成功`);
      } else if (status === 'error') {
        setUploading(false);
        message.error(`${info.file.name} 文件上传失败`);
      }
    },
  };

  return (
    <div className="upload-page">
      <PageHeader
        title="文件上传"
        onBack={() => history.goBack()}
      />

      <Dragger {...props} style={{ padding: 24 }}>
        <p className="ant-upload-drag-icon">
          <UploadOutlined />
        </p>
        <p className="ant-upload-text">点击或将文件拖拽到此区域上传</p>
        <p className="ant-upload-hint">
          仅支持上传.docx文件，支持批量上传
        </p>
      </Dragger>

      <Button
        type="primary"
        loading={uploading}
        onClick={() => history.goBack()}
        style={{ marginTop: 16 }}
      >
        返回
      </Button>
    </div>
  );
}

export default UploadPage;
