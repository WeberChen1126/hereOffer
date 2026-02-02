import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Upload, message, Space, Popconfirm, Card, Descriptions, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined, EyeOutlined, UploadOutlined, FileTextOutlined } from '@ant-design/icons';
import { knowledge } from '../services/api';
import type { UploadFile } from 'antd/es/upload/interface';

const { Dragger } = Upload;

interface Document {
  id: number;
  title: string;
  source: string;
  content: string;
  metadata_json?: {
    filename?: string;
    content_type?: string;
    size?: number;
  };
  created_at: string;
  updated_at: string;
}

const AdminKnowledgeManagement: React.FC = () => {
  const [list, setList] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadVisible, setUploadVisible] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentDoc, setCurrentDoc] = useState<Document | null>(null);
  const [uploading, setUploading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await knowledge.list();
      console.log('Knowledge documents response:', res);
      setList(res.data?.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      message.error('获取文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请选择要上传的文件');
      return;
    }

    const file = fileList[0].originFileObj;
    if (!file) {
      message.warning('文件无效');
      return;
    }

    // 检查文件类型
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const allowedExtensions = ['.pdf', '.docx', '.txt'];
    const fileName = file.name.toLowerCase();
    const isValidType = allowedTypes.includes(file.type) || 
                       allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidType) {
      message.error('不支持的文件格式，请上传 PDF、DOCX 或 TXT 文件');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      await knowledge.upload(formData);
      message.success('文档上传成功，正在处理中...');
      setUploadVisible(false);
      setFileList([]);
      fetchDocuments();
    } catch (error: any) {
      console.error('Failed to upload document:', error);
      message.error(error.response?.data?.detail || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      setLoading(true);
      await knowledge.delete(id);
      message.success('文档删除成功');
      fetchDocuments();
    } catch (error: any) {
      console.error('Failed to delete document:', error);
      message.error(error.response?.data?.detail || '删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (doc: Document) => {
    try {
      setLoading(true);
      const res = await knowledge.get(doc.id);
      setCurrentDoc(res.data);
      setDetailVisible(true);
    } catch (error) {
      console.error('Failed to fetch document detail:', error);
      message.error('获取文档详情失败');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '未知';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '文档名称',
      dataIndex: 'title',
      key: 'title',
      width: 250,
      render: (text: string) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <FileTextOutlined style={{ color: '#1890ff' }} />
          <span>{text}</span>
        </div>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 100,
      render: (source: string) => (
        <Tag color="blue">{source}</Tag>
      ),
    },
    {
      title: '文件大小',
      key: 'size',
      width: 120,
      render: (_: any, record: Document) => {
        const size = record.metadata_json?.size;
        return formatFileSize(size);
      },
    },
    {
      title: '内容预览',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text: string) => (
        <div style={{ maxHeight: 60, overflow: 'hidden' }}>
          {text.length > 100 ? text.substring(0, 100) + '...' : text}
        </div>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: Document) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Popconfirm
            title="确定删除此文档？"
            description="删除后将无法恢复，相关的向量数据也会被删除。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>知识库管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setUploadVisible(true)}
        >
          上传文档
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={list}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{ pageSize: 10 }}
      />

      {/* 上传文档弹窗 */}
      <Modal
        title="上传知识库文档"
        open={uploadVisible}
        onOk={handleUpload}
        onCancel={() => {
          setUploadVisible(false);
          setFileList([]);
        }}
        okText="上传"
        cancelText="取消"
        confirmLoading={uploading}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <p style={{ color: '#666', marginBottom: 8 }}>
            支持格式：PDF、DOCX、TXT
          </p>
          <p style={{ color: '#999', fontSize: 12 }}>
            上传后系统将自动提取文本、分块、向量化并存储到知识库中。
          </p>
        </div>
        <Dragger
          fileList={fileList}
          beforeUpload={() => false} // 阻止自动上传
          onChange={({ fileList: newFileList }) => {
            setFileList(newFileList);
          }}
          maxCount={1}
          accept=".pdf,.docx,.txt"
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个文件上传，文件格式：PDF、DOCX、TXT
          </p>
        </Dragger>
      </Modal>

      {/* 文档详情弹窗 */}
      <Modal
        title="文档详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={900}
      >
        {currentDoc && (
          <div>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="文档ID">{currentDoc.id}</Descriptions.Item>
              <Descriptions.Item label="文档名称">{currentDoc.title}</Descriptions.Item>
              <Descriptions.Item label="来源">
                <Tag color="blue">{currentDoc.source}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="文件大小">
                {formatFileSize(currentDoc.metadata_json?.size)}
              </Descriptions.Item>
              <Descriptions.Item label="文件类型" span={2}>
                {currentDoc.metadata_json?.content_type || '未知'}
              </Descriptions.Item>
              <Descriptions.Item label="上传时间" span={2}>
                {new Date(currentDoc.created_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
            </Descriptions>

            <Card
              title="📄 文档内容"
              size="small"
              style={{ marginTop: 16 }}
              headStyle={{ background: '#f5f5f5' }}
            >
              <div
                style={{
                  maxHeight: 500,
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.6,
                  padding: 12,
                  background: '#fafafa',
                  borderRadius: 4,
                }}
              >
                {currentDoc.content}
              </div>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AdminKnowledgeManagement;
