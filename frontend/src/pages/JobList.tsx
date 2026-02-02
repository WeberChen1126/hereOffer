import React, { useEffect, useState } from 'react';
import { List, Card, Button, Modal, Upload, message, Tag } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { jobs, applications } from '../services/api';
import { Job } from '../types';
import { useNavigate } from 'react-router-dom';

const JobList: React.FC = () => {
  const [list, setList] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [fileList, setFileList] = useState<any[]>([]);
  const navigate = useNavigate();

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await jobs.list({ is_active: true });
      console.log('API Response:', res); // 调试日志
      const jobsData = res.data?.jobs || res.data?.items || [];
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

  const handleApply = (jobId: number) => {
    setSelectedJobId(jobId);
    setApplyModalOpen(true);
  };

  const submitApplication = async () => {
    if (!selectedJobId || fileList.length === 0) {
      message.error('请选择简历文件');
      return;
    }
    const formData = new FormData();
    formData.append('job_id', selectedJobId.toString());
    formData.append('file', fileList[0].originFileObj); // 修改字段名为 'file'

    try {
      await applications.create(formData);
      message.success('投递成功');
      setApplyModalOpen(false);
      setFileList([]);
      navigate('/applications');
    } catch (error) {
      // error handled
      console.error('Failed to submit application:', error);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>职位列表</h2>
      <List
        grid={{ gutter: 16, column: 3 }}
        dataSource={list}
        loading={loading}
        renderItem={(item) => (
          <List.Item>
            <Card title={item.title} extra={<Tag color={item.is_active ? 'green' : 'red'}>{item.is_active ? '招聘中' : '已停止'}</Tag>}>
              <div style={{ height: 100, overflow: 'hidden', marginBottom: 16 }}>
                {item.description}
              </div>
              <Button type="primary" block onClick={() => handleApply(item.id)} disabled={!item.is_active}>
                立即投递
              </Button>
            </Card>
          </List.Item>
        )}
      />

      <Modal
        title="投递简历"
        open={applyModalOpen}
        onOk={submitApplication}
        onCancel={() => setApplyModalOpen(false)}
      >
        <Upload
          fileList={fileList}
          beforeUpload={() => false}
          onChange={({ fileList }) => setFileList(fileList.slice(-1))}
        >
          <Button icon={<UploadOutlined />}>上传简历 (PDF/Word/Txt)</Button>
        </Upload>
      </Modal>
    </div>
  );
};

export default JobList;
