import React, { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, InputNumber, Switch, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { jobs } from '../services/api';
import { Job } from '../types';

const { TextArea } = Input;

const AdminJobManagement: React.FC = () => {
  const [list, setList] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [form] = Form.useForm();

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await jobs.list();
      console.log('Admin jobs response:', res);
      const jobsData = res.data?.jobs || [];
      setList(jobsData);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
      message.error('获取职位列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleCreate = () => {
    setEditingJob(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (job: Job) => {
    setEditingJob(job);
    form.setFieldsValue(job);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      // 通过设置 is_active = false 来"删除"
      await jobs.update(id, { is_active: false });
      message.success('职位已停用');
      fetchJobs();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingJob) {
        // 更新
        await jobs.update(editingJob.id, values);
        message.success('职位更新成功');
      } else {
        // 创建
        await jobs.create(values);
        message.success('职位创建成功');
      }
      
      setModalVisible(false);
      fetchJobs();
    } catch (error) {
      console.error('Failed to submit:', error);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '职位名称',
      dataIndex: 'title',
      key: 'title',
      width: 200,
    },
    {
      title: '职位描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => (
        <div style={{ maxHeight: 60, overflow: 'hidden' }}>{text}</div>
      ),
    },
    {
      title: '评分阈值',
      dataIndex: 'threshold_score',
      key: 'threshold_score',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <span style={{ color: isActive ? 'green' : 'red' }}>
          {isActive ? '✓ 激活' : '✗ 停用'}
        </span>
      ),
    },
    {
      title: '创建时间',
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
      render: (_: any, record: Job) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          {record.is_active && (
            <Popconfirm
              title="确定停用此职位？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button 
                type="link" 
                size="small"
                danger
                icon={<DeleteOutlined />}
              >
                停用
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>职位管理</h2>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          创建职位
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

      <Modal
        title={editingJob ? '编辑职位' : '创建职位'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            threshold_score: 60,
            is_active: true,
          }}
        >
          <Form.Item
            name="title"
            label="职位名称"
            rules={[{ required: true, message: '请输入职位名称' }]}
          >
            <Input placeholder="例如：Python 后端工程师" />
          </Form.Item>

          <Form.Item
            name="description"
            label="职位描述"
            rules={[{ required: true, message: '请输入职位描述' }]}
          >
            <TextArea 
              rows={6} 
              placeholder="输入职位描述、要求、职责等..."
            />
          </Form.Item>

          <Form.Item
            name="threshold_score"
            label="评分阈值"
            rules={[{ required: true, message: '请输入评分阈值' }]}
          >
            <InputNumber 
              min={0} 
              max={100} 
              style={{ width: '100%' }}
              placeholder="0-100"
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="是否激活"
            valuePropName="checked"
          >
            <Switch checkedChildren="激活" unCheckedChildren="停用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AdminJobManagement;
